"""Verification of AI output against the brand knowledge actually supplied.

Centrally controlled contract file. Pydantic only proves the response has the
right *shape*. This module proves the response is *grounded*:

1. Every guideline / fact code must exist in the supplied BrandKnowledge.
   Unknown codes are removed and recorded in ``reference_note``.
2. Every quoted ``original_text`` must occur in the submitted content.
3. A ``confirmed_rule_violation`` must have a verified reference AND a located
   quote, otherwise it is downgraded to ``potential_issue``. An unsupported
   claim is never upgraded to a violation: missing evidence is not proof that
   a claim is false.
4. ``evidence`` is always rebuilt server-side from the verbatim text of the
   cited knowledge, so the model cannot fabricate evidence.
5. Overall status is derived deterministically from verified findings, never
   copied from the model.
6. Em dashes are normalised out of all model-written text (design rule 9).
"""

import re
from dataclasses import dataclass, field

from app.enums import SEVERITY_RANK, AIStatus, FindingSource, FindingType, OverallStatus, Severity
from app.schemas import AIAnalysisOutput, AIFinding, BrandKnowledge, FindingDraft

_QUOTE_MAP = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
_EM_DASH = re.compile(r"\s*\u2014\s*")


def sanitize_text(text: str | None) -> str | None:
    """Trim and replace em dashes (and en dashes) with plain punctuation."""
    if text is None:
        return None
    text = _EM_DASH.sub(", ", text).replace("\u2013", "-")
    return text.strip()


def normalise_code(code: str | None) -> str | None:
    if code is None:
        return None
    code = code.strip().upper()
    return code or None


def locate(quote: str, content: str) -> tuple[int, int] | None:
    """Case-insensitive search that tolerates curly vs straight quotes.
    The translation is 1:1 per character, so offsets map back to ``content``."""
    needle = quote.strip().translate(_QUOTE_MAP).lower()
    if not needle:
        return None
    start = content.translate(_QUOTE_MAP).lower().find(needle)
    if start < 0:
        return None
    return start, start + len(needle)


def build_evidence(knowledge: BrandKnowledge, guideline_id: str | None, approved_fact_id: str | None) -> str | None:
    parts: list[str] = []
    if guideline_id:
        g = next((g for g in knowledge.guidelines if g.id == guideline_id), None)
        if g:
            parts.append(f"{g.id}: {g.text}")
    if approved_fact_id:
        f = next((f for f in knowledge.facts if f.id == approved_fact_id), None)
        if f:
            parts.append(f"{f.id}: {f.statement}")
    return " ".join(parts) or None


@dataclass
class VerificationResult:
    findings: list[FindingDraft]
    notes: list[str] = field(default_factory=list)

    @property
    def had_corrections(self) -> bool:
        return bool(self.notes)


def _verify_one(finding: AIFinding, knowledge: BrandKnowledge, content: str) -> FindingDraft:
    notes: list[str] = []
    guideline_codes, fact_codes, term_codes = (
        knowledge.guideline_codes(),
        knowledge.fact_codes(),
        knowledge.term_codes(),
    )

    g = normalise_code(finding.guideline_id)
    f = normalise_code(finding.approved_fact_id)
    t: str | None = None

    # Tolerate a valid code placed in the wrong field.
    if g and g not in guideline_codes:
        if g in fact_codes and not f:
            f, g = g, None
        elif g in term_codes:
            t, g = g, None
    if f and f not in fact_codes and f in guideline_codes and not g:
        g, f = f, None

    if g and g not in guideline_codes:
        notes.append(f"The model cited guideline {g}, which is not in the approved brand knowledge. The reference was removed.")
        g = None
    if f and f not in fact_codes:
        notes.append(f"The model cited fact {f}, which is not in the approved brand knowledge. The reference was removed.")
        f = None

    span = locate(finding.original_text, content)
    if span is None and finding.finding_type != FindingType.RECOMMENDATION:
        notes.append("The quoted text could not be found in the submitted content.")

    finding_type = finding.finding_type
    if finding_type == FindingType.CONFIRMED_RULE_VIOLATION and (not (g or f) or span is None):
        finding_type = FindingType.POTENTIAL_ISSUE
        notes.append("Downgraded from confirmed violation to potential issue because it is not backed by a verified reference and a located quote.")
    elif finding_type == FindingType.UNSUPPORTED_CLAIM and span is None:
        finding_type = FindingType.POTENTIAL_ISSUE
        notes.append("Downgraded from unsupported claim to potential issue because the claim could not be located.")

    return FindingDraft(
        source=FindingSource.AI,
        category=finding.category,
        severity=finding.severity,
        finding_type=finding_type,
        original_text=sanitize_text(finding.original_text) or "",
        start_offset=span[0] if span else None,
        end_offset=span[1] if span else None,
        guideline_id=g,
        approved_fact_id=f,
        approved_term_id=t,
        evidence=build_evidence(knowledge, g, f),
        explanation=sanitize_text(finding.explanation) or "",
        suggestion=sanitize_text(finding.suggestion),
        confidence=finding.confidence,
        reference_note=" ".join(notes) or None,
    )


def verify_ai_findings(output: AIAnalysisOutput, knowledge: BrandKnowledge, content: str) -> VerificationResult:
    findings = [_verify_one(f, knowledge, content) for f in output.findings]
    notes = [f.reference_note for f in findings if f.reference_note]
    return VerificationResult(findings=findings, notes=notes)


def derive_overall_status(findings: list[FindingDraft], ai_status: AIStatus) -> OverallStatus:
    """Deterministic status policy (documented in docs/api-contract.md).

    non_compliant: any confirmed_rule_violation of medium severity or above.
    needs_review:  any unsupported claim, any lower-severity confirmed
                   violation, any potential issue of medium or above, or the
                   contextual AI analysis did not complete.
    compliant:     otherwise (only recommendations / minor observations).
    """
    medium = SEVERITY_RANK[Severity.MEDIUM]
    if any(
        f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION and SEVERITY_RANK[f.severity] >= medium
        for f in findings
    ):
        return OverallStatus.NON_COMPLIANT
    if (
        ai_status != AIStatus.OK
        or any(f.finding_type in (FindingType.UNSUPPORTED_CLAIM, FindingType.CONFIRMED_RULE_VIOLATION) for f in findings)
        or any(f.finding_type == FindingType.POTENTIAL_ISSUE and SEVERITY_RANK[f.severity] >= medium for f in findings)
    ):
        return OverallStatus.NEEDS_REVIEW
    return OverallStatus.COMPLIANT


def derive_requires_human_review(
    status: OverallStatus, ai_status: AIStatus, verification: VerificationResult | None, ai_flag: bool
) -> bool:
    return (
        status != OverallStatus.COMPLIANT
        or ai_status != AIStatus.OK
        or ai_flag
        or bool(verification and verification.had_corrections)
    )
