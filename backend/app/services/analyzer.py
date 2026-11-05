"""Unified analysis engine combining deterministic rules and Gemini AI.

Pipeline:
1. Run deterministic rule engine.
2. Run Gemini AI analysis (or handle fallback if disabled/unavailable).
3. Merge and deduplicate findings:
   - Rule engine findings take priority when spans or codes overlap.
   - Verified Gemini findings complement rule engine with semantic observations.
4. Derive overall status and human review necessity deterministically.
"""

import time
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.enums import AIStatus, FindingSource, OverallStatus
from app.schemas import BrandKnowledge, FindingDraft
from app.services.gemini_service import run_gemini_analysis
from app.services.rule_engine import run_rule_engine
from app.validation import derive_overall_status, derive_requires_human_review

RULE_ENGINE_VERSION = "1.0.0"


@dataclass
class CompleteAnalysisResult:
    overall_status: OverallStatus
    summary: str
    positive_observations: list[str]
    requires_human_review: bool
    ai_status: AIStatus
    model_name: str | None
    rule_engine_version: str
    knowledge_snapshot: dict[str, Any]
    duration_ms: int
    findings: list[FindingDraft]


def _deduplicate_findings(
    rule_findings: list[FindingDraft],
    ai_findings: list[FindingDraft],
) -> list[FindingDraft]:
    """Merges findings while avoiding duplicate reporting of the same text span."""
    combined = list(rule_findings)

    for ai_f in ai_findings:
        # Check if an existing rule finding already covers this exact span or text
        is_covered = False
        for rf in combined:
            if rf.start_offset is not None and ai_f.start_offset is not None:
                # Overlapping text span
                if max(rf.start_offset, ai_f.start_offset) < min(rf.end_offset or 0, ai_f.end_offset or 0):
                    is_covered = True
                    break
            elif rf.original_text.lower() in ai_f.original_text.lower() or ai_f.original_text.lower() in rf.original_text.lower():
                if rf.guideline_id == ai_f.guideline_id or rf.approved_fact_id == ai_f.approved_fact_id:
                    is_covered = True
                    break

        if not is_covered:
            combined.append(ai_f)

    return combined


def analyze_content(
    content: str,
    knowledge: BrandKnowledge,
) -> CompleteAnalysisResult:
    """Runs complete hybrid compliance analysis on content against BrandKnowledge."""
    start_time = time.perf_counter()
    settings = get_settings()

    # Step 1: Deterministic rule engine
    rule_findings, rule_positives = run_rule_engine(content, knowledge)

    # Step 2: Gemini LLM analysis
    ai_raw, ai_verification, ai_status, ai_error = run_gemini_analysis(content, knowledge)

    ai_findings = ai_verification.findings if ai_verification else []
    ai_positives = ai_raw.positive_observations if ai_raw else []

    # Step 3: Merge findings and observations
    all_findings = _deduplicate_findings(rule_findings, ai_findings)

    # Combine positive observations, preserving uniqueness
    combined_positives = list(rule_positives)
    for p in ai_positives:
        clean_p = p.strip()
        if clean_p and clean_p not in combined_positives:
            combined_positives.append(clean_p)

    # Step 4: Status determination
    overall_status = derive_overall_status(all_findings, ai_status)

    ai_flagged_review = ai_raw.requires_human_review if ai_raw else False
    requires_human_review = derive_requires_human_review(
        overall_status, ai_status, ai_verification, ai_flagged_review
    )

    # Step 5: Summary text
    if ai_raw and ai_raw.summary:
        summary = ai_raw.summary
    else:
        # Fallback summary based on findings
        count = len(all_findings)
        if overall_status == OverallStatus.COMPLIANT:
            summary = "Content aligns with approved brand guidelines and factual standards."
        elif overall_status == OverallStatus.NON_COMPLIANT:
            summary = f"Content contains {count} brand compliance issue(s), including confirmed rule violations."
        else:
            summary = f"Content requires review: {count} potential issue(s) or unsupported claim(s) detected."

        if ai_status == AIStatus.UNAVAILABLE and ai_error:
            summary += f" [AI Engine unavailable: {ai_error}]"

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    return CompleteAnalysisResult(
        overall_status=overall_status,
        summary=summary,
        positive_observations=combined_positives,
        requires_human_review=requires_human_review,
        ai_status=ai_status,
        model_name=settings.gemini_model if ai_status == AIStatus.OK else None,
        rule_engine_version=RULE_ENGINE_VERSION,
        knowledge_snapshot=knowledge.model_dump(mode="json"),
        duration_ms=duration_ms,
        findings=all_findings,
    )
