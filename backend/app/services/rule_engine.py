"""Deterministic rule engine for brand compliance analysis.

Evaluates content against brand knowledge without depending on an LLM:
1. Exact prohibited terminology (case & punctuation normalised).
2. Explicit guarantee language regarding medical / skincare outcomes (GUIDE-001).
3. Explicit unapproved acne-removal timeframes (FACT-002, e.g., 'within X days', 'in X days').
4. Preferred terminology recognition (positive observations).
5. Exaggerated outcome claims ('flawless skin instantly', 'cure acne').
"""

import re
from typing import Sequence

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import BrandKnowledge, FindingDraft, Guideline, Term
from app.services.relevance import (
    BrandRelevance,
    assess_brand_relevance,
    make_insufficient_context_finding,
    make_unrelated_finding,
)
from app.validation import build_evidence, locate, sanitize_text

# Regex patterns for deterministic checks
NUMBER_WORDS = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty-four|forty-eight)"
TIMEFRAME_PATTERN = re.compile(
    r"\b(?:in\s+(?:just\s+)?|within\s+(?:just\s+)?|after\s+)"
    + NUMBER_WORDS
    + r"\s*(?:days?|hours?|weeks?)\b",
    re.IGNORECASE,
)

GUARANTEE_PATTERN = re.compile(
    r"\b(?:guarantees?|guaranteed|100%\s+guarantee|instant(?:ly)?\s+cure)\b",
    re.IGNORECASE,
)

UNAPPROVED_ACNE_CLAIM_PATTERN = re.compile(
    r"\b(?:reduces?|eliminates?|cures?|removes?)\s+acne\b",
    re.IGNORECASE,
)

EXAGGERATED_CLAIMS = [
    (re.compile(r"\bflawless\s+skin\s+instantly\b", re.IGNORECASE), "Exaggerated claim of instant perfection."),
    (re.compile(r"\brevolutionary\s+cream\s+guarantees\b", re.IGNORECASE), "Unsubstantiated superlative with guarantee."),
]


def _build_term_regex(term_text: str) -> re.Pattern[str]:
    """Builds a flexible regex for a terminology phrase, handling common inflections
    (e.g., guarantee/guarantees/guaranteed, support/supports) and hyphen/space variations."""
    words = term_text.strip().split()
    regex_parts = []
    for w in words:
        w_lower = w.lower()
        if w_lower in ("guaranteed", "guarantee", "guarantees"):
            regex_parts.append(r"guarantees?(?:d)?(?:\s+\d+%?)?")
        elif w_lower in ("supports", "support"):
            regex_parts.append(r"supports?")
        elif "-" in w_lower:
            parts = [re.escape(p) for p in w_lower.split("-")]
            regex_parts.append(r"[-\s]".join(parts))
        else:
            regex_parts.append(re.escape(w_lower))
    pattern_str = r"\b" + r"\s+".join(regex_parts) + r"\b"
    return re.compile(pattern_str, re.IGNORECASE)


def _find_guideline_by_code(guidelines: Sequence[Guideline], code: str) -> Guideline | None:
    return next((g for g in guidelines if g.id == code), None)


def _has_brand_substance(content: str, knowledge: BrandKnowledge) -> bool:
    """Checks whether the text contains substantive references to the brand,
    its products, approved terminology, or domain concepts derived dynamically
    from the brand's knowledge base."""
    text = content.lower()

    if knowledge.brand_name.lower() in text:
        return True

    for t in knowledge.terms:
        if t.preferred_term and t.preferred_term.lower() in text:
            return True
        if t.prohibited_term and t.prohibited_term.lower() in text:
            return True

    # Dynamically extract substantive vocabulary from the brand's guidelines and facts
    stop_words = {
        "this", "that", "with", "from", "your", "have", "been", "must", "will", "more",
        "some", "such", "than", "then", "into", "only", "also", "when", "what", "which",
        "about", "after", "other", "their", "there", "these", "those", "would", "could",
        "should", "brand", "approved", "statement", "information", "guideline", "guidelines"
    }
    substantive_tokens: set[str] = set()
    for f in knowledge.facts:
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", f.statement.lower()):
            if word not in stop_words:
                substantive_tokens.add(word)
    for g in knowledge.guidelines:
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", g.text.lower()):
            if word not in stop_words:
                substantive_tokens.add(word)

    return any(re.search(rf"\b{re.escape(token)}\b", text) for token in substantive_tokens)


def run_rule_engine(
    content: str,
    knowledge: BrandKnowledge,
) -> tuple[list[FindingDraft], list[str]]:
    """Runs deterministic checks on content against supplied BrandKnowledge.

    Returns:
        tuple of (findings, positive_observations)
    """
    relevance = assess_brand_relevance(content, knowledge)
    if relevance.status == BrandRelevance.UNRELATED:
        return [make_unrelated_finding(content, knowledge)], []
    if relevance.status == BrandRelevance.INSUFFICIENT_CONTEXT:
        return [make_insufficient_context_finding(content, knowledge)], []

    findings: list[FindingDraft] = []
    positive_observations: list[str] = []

    # 1. Prohibited Terminology Checks
    for term in knowledge.terms:
        if term.prohibited_term:
            prohibited_raw = term.prohibited_term.strip()
            regex = _build_term_regex(prohibited_raw)
            match = regex.search(content)
            if match:
                start, end = match.start(), match.end()
                actual_quote = content[start:end]
                related_guide = term.related_guideline_id or "GUIDE-001"
                evidence_text = build_evidence(knowledge, related_guide, None)
                findings.append(
                    FindingDraft(
                        source=FindingSource.RULE_ENGINE,
                        category=FindingCategory.TERMINOLOGY,
                        severity=Severity.HIGH,
                        finding_type=FindingType.CONFIRMED_RULE_VIOLATION,
                        original_text=actual_quote,
                        start_offset=start,
                        end_offset=end,
                        guideline_id=related_guide,
                        approved_term_id=term.id,
                        evidence=evidence_text,
                        explanation=sanitize_text(
                            f"Contains prohibited terminology: '{actual_quote}'. "
                            f"Approved preference is '{term.preferred_term}'."
                        ) or "",
                        suggestion=f"Replace with approved phrasing: '{term.preferred_term}'.",
                        confidence=1.0,
                    )
                )

        # Check for Preferred Term usage
        if term.preferred_term:
            preferred_raw = term.preferred_term.strip()
            pref_regex = _build_term_regex(preferred_raw)
            pref_match = pref_regex.search(content)
            if pref_match:
                start, end = pref_match.start(), pref_match.end()
                matched_quote = content[start:end]
                positive_observations.append(
                    f"Aligns with preferred terminology '{term.preferred_term}': '{matched_quote}'."
                )

    # 2. Timeframe violations against FACT-002
    # FACT-002: "No guaranteed acne-removal timeframe has been approved."
    if "FACT-002" in knowledge.fact_codes():
        for match in TIMEFRAME_PATTERN.finditer(content):
            matched_text = match.group(0)
            start, end = match.start(), match.end()
            # If "guarantee" or "acne" is nearby or in content, this is high severity
            is_high = bool(re.search(r"acne|guarantee", content, re.IGNORECASE))
            evidence_text = build_evidence(knowledge, "GUIDE-003", "FACT-002")
            findings.append(
                FindingDraft(
                    source=FindingSource.RULE_ENGINE,
                    category=FindingCategory.TIMEFRAME,
                    severity=Severity.HIGH if is_high else Severity.MEDIUM,
                    finding_type=FindingType.UNSUPPORTED_CLAIM,
                    original_text=matched_text,
                    start_offset=start,
                    end_offset=end,
                    guideline_id="GUIDE-003",
                    approved_fact_id="FACT-002",
                    evidence=evidence_text,
                    explanation=sanitize_text(
                        f"Specific timeframe '{matched_text}' is not an approved timeframe. "
                        "No specific outcome timeframe has been clinically approved."
                    ) or "",
                    suggestion="Remove the specific timeframe claim or qualify as a general skincare routine addition.",
                    confidence=0.95,
                )
            )

    # 3. Explicit Guarantee / Outcome Violations (GUIDE-001)
    if "GUIDE-001" in knowledge.guideline_codes():
        for match in GUARANTEE_PATTERN.finditer(content):
            matched_text = match.group(0)
            start, end = match.start(), match.end()
            # Expand to surrounding phrase if possible
            phrase_start = max(0, start - 15)
            phrase_end = min(len(content), end + 25)
            sentence_slice = content[phrase_start:phrase_end].strip()

            # Avoid duplicating an existing prohibited term finding on the same span
            if not any(f.start_offset is not None and abs(f.start_offset - start) < 10 for f in findings):
                evidence_text = build_evidence(knowledge, "GUIDE-001", None)
                findings.append(
                    FindingDraft(
                        source=FindingSource.RULE_ENGINE,
                        category=FindingCategory.OUTCOME_CLAIM,
                        severity=Severity.HIGH,
                        finding_type=FindingType.CONFIRMED_RULE_VIOLATION,
                        original_text=sentence_slice,
                        start_offset=start,
                        end_offset=end,
                        guideline_id="GUIDE-001",
                        evidence=evidence_text,
                        explanation=sanitize_text(
                            f"Contains promise of guaranteed outcome: '{matched_text}'. "
                            "Brand guidelines prohibit promising guaranteed skincare outcomes."
                        ) or "",
                        suggestion="Reframe without guarantee terms (e.g., 'designed to support clearer-looking skin').",
                        confidence=0.95,
                    )
                )

    # 4. Exaggerated claims
    for regex, explanation in EXAGGERATED_CLAIMS:
        for match in regex.finditer(content):
            start, end = match.start(), match.end()
            if not any(f.start_offset is not None and abs(f.start_offset - start) < 5 for f in findings):
                evidence_text = build_evidence(knowledge, "GUIDE-002", None)
                findings.append(
                    FindingDraft(
                        source=FindingSource.RULE_ENGINE,
                        category=FindingCategory.TONE,
                        severity=Severity.HIGH,
                        finding_type=FindingType.CONFIRMED_RULE_VIOLATION,
                        original_text=match.group(0),
                        start_offset=start,
                        end_offset=end,
                        guideline_id="GUIDE-002",
                        evidence=evidence_text,
                        explanation=sanitize_text(explanation) or "",
                        suggestion="Adopt friendly, realistic messaging.",
                        confidence=0.9,
                    )
                )

    # 4b. Unapproved acne claims (e.g. "reduces acne") against FACT-001/FACT-002
    if "FACT-001" in knowledge.fact_codes():
        for match in UNAPPROVED_ACNE_CLAIM_PATTERN.finditer(content):
            matched_text = match.group(0)
            start, end = match.start(), match.end()
            if not any(f.start_offset is not None and abs(f.start_offset - start) < 10 for f in findings):
                evidence_text = build_evidence(knowledge, "GUIDE-003", "FACT-001")
                findings.append(
                    FindingDraft(
                        source=FindingSource.RULE_ENGINE,
                        category=FindingCategory.OUTCOME_CLAIM,
                        severity=Severity.MEDIUM,
                        finding_type=FindingType.UNSUPPORTED_CLAIM,
                        original_text=matched_text,
                        start_offset=start,
                        end_offset=end,
                        guideline_id="GUIDE-003",
                        approved_fact_id="FACT-001",
                        evidence=evidence_text,
                        explanation=sanitize_text(
                            f"Claim '{matched_text}' lacks approved supporting evidence in brand facts. "
                            "Approved messaging states the product is designed to support clearer-looking skin."
                        ) or "",
                        suggestion="Replace with approved messaging: 'designed to support clearer-looking skin'.",
                        confidence=0.95,
                    )
                )

    # 5. Tone check positive observation
    if "gentle, reassuring approach" in content.lower() or "simple addition to your skincare routine" in content.lower():
        positive_observations.append("Reflects friendly, reassuring and realistic tone aligned with brand guidelines.")

    # 6. Insufficient context check
    # Distinguishes genuinely compliant content from content that lacks sufficient context for meaningful assessment.
    # If no rule violations were detected, verify that the content has sufficient brand/product substance.
    words = content.strip().split()
    if len(findings) == 0:
        is_too_short = len(words) < 3
        is_generic_or_empty = len(words) < 10 and not _has_brand_substance(content, knowledge)
        if is_too_short or is_generic_or_empty:
            findings.append(
                FindingDraft(
                    source=FindingSource.RULE_ENGINE,
                    category=FindingCategory.OTHER,
                    severity=Severity.MEDIUM,
                    finding_type=FindingType.POTENTIAL_ISSUE,
                    original_text=content.strip(),
                    start_offset=0,
                    end_offset=len(content),
                    guideline_id=None,
                    approved_fact_id=None,
                    evidence="Brand governance requires sufficient communication context to evaluate compliance against approved brand standards.",
                    explanation=(
                        f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable "
                        "governance assessment. Short, greeting, or generic copy requires human review before approval."
                    ),
                    suggestion="Provide substantive communication copy including relevant brand messaging or product context.",
                    confidence=0.95,
                )
            )

    return findings, positive_observations
