"""Gemini LLM integration for semantic brand compliance analysis.

Uses Google GenAI SDK with structured outputs (AIAnalysisOutput).
Safe execution:
- Never crashes the caller.
- Catches network, quota, schema and timeout errors, returning appropriate AIStatus.
- Sanitises output and verifies grounding with app.validation.verify_ai_findings.
"""

import logging
import re
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
1. ONLY cite guidelines and facts provided in the knowledge base below.
2. NEVER invent guideline IDs, fact IDs, or brand rules.
3. Every cited quote in 'original_text' MUST appear verbatim in the submitted content.
4. Distinguish between 'confirmed_rule_violation' (direct contradiction of a rule) and 'unsupported_claim' (a claim not backed by facts, but not necessarily contradictory).
5. Missing evidence is NOT proof that a claim is false, but an unsupported claim needs review.
6. Acknowledge positive brand alignment in 'positive_observations' (e.g. usage of preferred terms or reassuring tone).
7. Do not flag harmless, realistic descriptions as violations.
8. DO NOT use em dashes in explanations or suggestions. Use commas, semicolons, or hyphens instead.
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
            http_options=types.HttpOptions(timeout=settings.gemini_timeout_seconds),
        )
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AIAnalysisOutput,
            temperature=0.0,
        )

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )

        if not response.text:
            logger.warning("Empty response from Gemini API")
            return None, None, AIStatus.INVALID_RESPONSE, "Empty response from model."

        parsed_output = AIAnalysisOutput.model_validate_json(response.text)
        verification = verify_ai_findings(parsed_output, knowledge, content)

        return parsed_output, verification, AIStatus.OK, None

    except Exception as exc:
        clean_err = sanitize_error(exc)
        logger.warning("Gemini analysis failed or timed out: %s (%s)", type(exc).__name__, clean_err)
        return None, None, AIStatus.UNAVAILABLE, f"{type(exc).__name__}: {clean_err}"
