"""Gemini LLM integration for semantic brand compliance analysis.

Uses Google GenAI SDK with structured outputs (AIAnalysisOutput).
Safe execution:
- Never crashes the caller.
- Catches network, quota, schema and timeout errors, returning appropriate AIStatus.
- Sanitises output and verifies grounding with app.validation.verify_ai_findings.
"""

import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types

from app.config import get_settings
from app.enums import AIStatus
from app.schemas import AIAnalysisOutput, BrandKnowledge
from app.validation import VerificationResult, verify_ai_findings

logger = logging.getLogger(__name__)


def sanitize_error(err: Exception | str) -> str:
    text = str(err)
    return re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)

SYSTEM_PROMPT = """You are Inkloom AI, an intelligent brand-governance engine.
Your mission is to evaluate marketing and communication content strictly against the provided brand knowledge.

RULES:
1. Evaluate the ACTUAL submitted text objectively on its own merits, independently of any test scenarios or templates.
2. ONLY cite guidelines and facts provided in the knowledge base below. NEVER invent guideline IDs, fact IDs, or brand rules.
3. Every cited quote in 'original_text' MUST appear verbatim in the submitted content.
4. Distinguish between 'confirmed_rule_violation' (direct contradiction of a rule) and 'unsupported_claim' (a claim not backed by facts, such as unapproved timeframes like '7 days' or 'seven days').
5. Missing evidence is NOT proof that a claim is false, but an unsupported claim needs review.
6. INSUFFICIENT CONTEXT: If the submitted content is very short, meaningless, conversational filler, or a generic pleasantry (such as greetings like 'Have a beautiful day!' or single words like 'hellloooooooo') that completely lacks brand or product context for a meaningful governance assessment, DO NOT approve it as compliant. Instead, add a finding with category 'other', severity 'medium', finding_type 'potential_issue', and set requires_human_review to true, explaining that the content lacks sufficient brand context for an automated brand governance assessment.
7. Only mark content as compliant (zero findings) if it contains substantive communication that genuinely adheres to approved brand guidelines, facts, and voice standards.
8. Acknowledge positive brand alignment in 'positive_observations' (e.g. usage of preferred terms or reassuring tone).
9. Do not flag harmless, realistic descriptions as violations.
10. DO NOT use em dashes in explanations or suggestions. Use commas, semicolons, or hyphens instead.
11. UNIVERSAL BRAND IDENTITY: Always evaluate content strictly for the active brand. If the submitted content solely describes, introduces, or belongs to another brand, company, or organization (regardless of whether it is in the same industry such as another skincare brand, or a different industry such as fintech, food, clothing, or electronics) and does not substantively discuss the active brand: DO NOT evaluate it against the active brand's guidelines, and DO NOT generate active brand violations or corrections for it. Instead, set requires_human_review to true, and add a single finding with category 'other', severity 'high', finding_type 'potential_issue', reference_note 'Reason code: UNRELATED_TO_BRAND', explaining that the content belongs to another brand and cannot be assessed against the active brand.
12. COMPETITOR COMPARISONS AND MULTI-BRAND CONTEXT: When submitted content discusses the active brand in comparison with competitors, alternative brands, or market peers:
    - The content IS RELEVANT to the active brand. Do NOT classify it as UNRELATED_TO_BRAND.
    - Evaluate statements made about the ACTIVE BRAND against the approved brand knowledge (guidelines, facts, and terminology).
    - DO NOT apply active brand guidelines or product rules to claims that exclusively describe a competitor or other brand (e.g. competitor outcome guarantees or competitor timeframes).
    - If the active brand makes unsupported comparative superiority claims over competitors without approved clinical evidence, classify them as 'unsupported_claim' with severity 'medium', requiring human review.
    - Recognize positive alignment with the active brand's positioning (such as realistic, transparent communication and preferred terminology) in 'positive_observations'.
"""


def _format_brand_knowledge(knowledge: BrandKnowledge) -> str:
    lines = [f"BRAND: {knowledge.brand_name}\n", "APPROVED GUIDELINES:"]
    for g in knowledge.guidelines:
        lines.append(f"- [{g.id}] {g.title} ({g.category}, severity: {g.default_severity}): {g.text}")

    lines.append("\nAPPROVED FACTS:")
    for f in knowledge.facts:
        lines.append(f"- [{f.id}]: {f.statement}")

    lines.append("\nAPPROVED / PROHIBITED TERMINOLOGY:")
    for t in knowledge.terms:
        parts = [f"- [{t.id}]"]
        if t.preferred_term:
            parts.append(f"Preferred: '{t.preferred_term}'")
        if t.prohibited_term:
            parts.append(f"Prohibited: '{t.prohibited_term}'")
        if t.notes:
            parts.append(f"Notes: {t.notes}")
        lines.append(" | ".join(parts))

    return "\n".join(lines)


def run_gemini_analysis(
    content: str,
    knowledge: BrandKnowledge,
) -> tuple[AIAnalysisOutput | None, VerificationResult | None, AIStatus, str | None]:
    """Runs Gemini structured analysis on content.

    Returns:
        tuple of (raw_output, verification_result, ai_status, error_detail)
    """
    settings = get_settings()

    if not settings.gemini_api_key:
        return None, None, AIStatus.DISABLED, "API key not configured."

    brand_context = _format_brand_knowledge(knowledge)
    prompt = f"""{brand_context}

SUBMITTED CONTENT TO ANALYSE:
\"\"\"
{content}
\"\"\"

Analyse the submitted content against the approved brand knowledge. Return a structured JSON compliance report.
"""

    try:
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(settings.gemini_timeout_seconds * 1000)),
        )
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AIAnalysisOutput,
            temperature=0.0,
        )

        # Try primary model first, with 1 retry on transient 503; then fall back to high-availability flash-lite
        candidate_models = [settings.gemini_model]
        if settings.gemini_model != "gemini-3.1-flash-lite":
            candidate_models.append("gemini-3.1-flash-lite")

        last_exc: Exception | None = None
        for model_id in candidate_models:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=prompt,
                        config=config,
                    )

                    if not response.text:
                        logger.warning("Empty response from Gemini API (%s)", model_id)
                        return None, None, AIStatus.INVALID_RESPONSE, "Empty response from model."

                    parsed_output = AIAnalysisOutput.model_validate_json(response.text)
                    verification = verify_ai_findings(parsed_output, knowledge, content)

                    return parsed_output, verification, AIStatus.OK, None

                except Exception as exc:
                    last_exc = exc
                    err_msg = str(exc)
                    # Transient capacity spike on Google side: brief delay and retry once
                    if ("503" in err_msg or "UNAVAILABLE" in err_msg) and attempt == 0:
                        logger.info("Transient 503 on %s, retrying after 1.5s...", model_id)
                        time.sleep(1.5)
                        continue
                    break

        if last_exc:
            raise last_exc
        return None, None, AIStatus.UNAVAILABLE, "No model succeeded."

    except Exception as exc:
        clean_err = sanitize_error(exc)
        logger.warning("Gemini analysis failed or timed out: %s (%s)", type(exc).__name__, clean_err)
        return None, None, AIStatus.UNAVAILABLE, f"{type(exc).__name__}: {clean_err}"
