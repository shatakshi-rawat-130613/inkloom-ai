"""Grounding and status-policy tests for app.validation."""

import pytest

from app.enums import AIStatus, FindingCategory, FindingSource, FindingType, OverallStatus, Severity
from app.schemas import AIAnalysisOutput, AIFinding, BrandKnowledge, Fact, FindingDraft, Guideline, Term
from app.validation import (
    derive_overall_status,
    derive_requires_human_review,
    locate,
    sanitize_text,
    verify_ai_findings,
)
from tests.fixtures.lumacare_cases import COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT

KNOWLEDGE = BrandKnowledge(
    brand_name="LumaCare",
    guidelines=[
        Guideline(id="GUIDE-001", title="t", text="Do not promise guaranteed medical or skincare outcomes.", category="outcome_claim", default_severity="high"),
        Guideline(id="GUIDE-002", title="t", text="Use friendly, reassuring and realistic messaging.", category="tone", default_severity="medium"),
        Guideline(id="GUIDE-003", title="t", text="Claims must be consistent with approved product information.", category="factual_consistency", default_severity="high"),
    ],
    facts=[
        Fact(id="FACT-001", statement="The product is designed to support clearer-looking skin.", source=None),
        Fact(id="FACT-002", statement="No guaranteed acne-removal timeframe has been approved.", source=None),
    ],
    terms=[Term(id="TERM-001", preferred_term="supports clearer-looking skin", prohibited_term="guaranteed acne removal", notes=None, related_guideline_id="GUIDE-001")],
)


def _ai(**kw) -> AIFinding:
    base = dict(category="outcome_claim", severity="high", finding_type="confirmed_rule_violation",
                original_text="guarantees 100% acne removal", guideline_id="GUIDE-001", approved_fact_id=None,
                explanation="Promises a guaranteed outcome \u2014 not allowed.", suggestion=None, confidence=0.9)
    base.update(kw)
    return AIFinding(**base)


def _verify(*findings, content=NON_COMPLIANT.content):
    out = AIAnalysisOutput(summary="s", findings=list(findings), positive_observations=[], requires_human_review=False)
    return verify_ai_findings(out, KNOWLEDGE, content)


def test_valid_reference_is_kept_with_server_side_evidence():
    (f,) = _verify(_ai()).findings
    assert f.guideline_id == "GUIDE-001"
    assert f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION
    assert f.evidence == "GUIDE-001: Do not promise guaranteed medical or skincare outcomes."
    assert f.reference_note is None
    assert NON_COMPLIANT.content[f.start_offset:f.end_offset].lower() == "guarantees 100% acne removal"


def test_fabricated_guideline_is_removed_and_violation_downgraded():
    result = _verify(_ai(guideline_id="GUIDE-999"))
    (f,) = result.findings
    assert f.guideline_id is None
    assert f.evidence is None
    assert f.finding_type == FindingType.POTENTIAL_ISSUE
    assert "GUIDE-999" in f.reference_note
    assert result.had_corrections


def test_fabricated_fact_is_removed_but_valid_guideline_kept():
    (f,) = _verify(_ai(approved_fact_id="FACT-042")).findings
    assert f.approved_fact_id is None and f.guideline_id == "GUIDE-001"
    assert f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION
    assert "FACT-042" in f.reference_note


def test_lowercase_and_misplaced_codes_are_normalised():
    (f,) = _verify(_ai(guideline_id=" fact-002 ")).findings
    assert f.guideline_id is None and f.approved_fact_id == "FACT-002"
    assert f.reference_note is None


def test_quote_not_in_content_downgrades_violation():
    (f,) = _verify(_ai(original_text="cures eczema overnight")).findings
    assert f.finding_type == FindingType.POTENTIAL_ISSUE
    assert f.start_offset is None
    assert "could not be found" in f.reference_note


def test_unsupported_claim_is_never_upgraded():
    (f,) = _verify(
        _ai(finding_type="unsupported_claim", original_text="helps reduce acne within 7 days", guideline_id="GUIDE-003", approved_fact_id="FACT-002"),
        content=PARTIALLY_COMPLIANT.content,
    ).findings
    assert f.finding_type == FindingType.UNSUPPORTED_CLAIM


def test_general_recommendation_without_quote_is_allowed():
    (f,) = _verify(_ai(finding_type="recommendation", severity="informational", original_text="", guideline_id=None)).findings
    assert f.finding_type == FindingType.RECOMMENDATION and f.reference_note is None


def test_em_dashes_removed_from_model_text():
    (f,) = _verify(_ai()).findings
    assert "\u2014" not in f.explanation
    assert sanitize_text("A \u2014 B") == "A, B"
    assert sanitize_text("2\u20133 days") == "2-3 days"


def test_locate_tolerates_case_and_curly_quotes():
    assert locate("It\u2019s GENTLE", "it's gentle care") == (0, 11)
    assert locate("absent", "text") is None


def _draft(ft: FindingType, sev: Severity) -> FindingDraft:
    return FindingDraft(source=FindingSource.RULE_ENGINE, category=FindingCategory.OTHER, severity=sev,
                        finding_type=ft, original_text="x", explanation="e", confidence=1.0)


@pytest.mark.parametrize(
    ("findings", "ai_status", "expected"),
    [
        # Test 1 shape: confirmed high-severity violation
        ([_draft(FindingType.CONFIRMED_RULE_VIOLATION, Severity.CRITICAL), _draft(FindingType.UNSUPPORTED_CLAIM, Severity.HIGH)], AIStatus.OK, OverallStatus.NON_COMPLIANT),
        # Test 2 shape: only an informational recommendation
        ([_draft(FindingType.RECOMMENDATION, Severity.INFORMATIONAL)], AIStatus.OK, OverallStatus.COMPLIANT),
        ([], AIStatus.OK, OverallStatus.COMPLIANT),
        # Test 3 shape: unsupported claim, no direct contradiction
        ([_draft(FindingType.UNSUPPORTED_CLAIM, Severity.HIGH)], AIStatus.OK, OverallStatus.NEEDS_REVIEW),
        ([_draft(FindingType.POTENTIAL_ISSUE, Severity.MEDIUM)], AIStatus.OK, OverallStatus.NEEDS_REVIEW),
        ([_draft(FindingType.POTENTIAL_ISSUE, Severity.LOW)], AIStatus.OK, OverallStatus.COMPLIANT),
        ([_draft(FindingType.CONFIRMED_RULE_VIOLATION, Severity.LOW)], AIStatus.OK, OverallStatus.NEEDS_REVIEW),
        # AI did not run: never claim compliant on rules alone
        ([], AIStatus.UNAVAILABLE, OverallStatus.NEEDS_REVIEW),
        ([], AIStatus.DISABLED, OverallStatus.NEEDS_REVIEW),
        # Rule violation still blocks even when AI failed
        ([_draft(FindingType.CONFIRMED_RULE_VIOLATION, Severity.HIGH)], AIStatus.INVALID_RESPONSE, OverallStatus.NON_COMPLIANT),
    ],
)
def test_overall_status_policy(findings, ai_status, expected):
    assert derive_overall_status(findings, ai_status) == expected


def test_requires_human_review_policy():
    assert derive_requires_human_review(OverallStatus.COMPLIANT, AIStatus.OK, None, False) is False
    assert derive_requires_human_review(OverallStatus.COMPLIANT, AIStatus.OK, None, True) is True
    assert derive_requires_human_review(OverallStatus.COMPLIANT, AIStatus.UNAVAILABLE, None, False) is True
    assert derive_requires_human_review(OverallStatus.NEEDS_REVIEW, AIStatus.OK, None, False) is True
    corrected = _verify(_ai(guideline_id="GUIDE-999"))
    assert derive_requires_human_review(OverallStatus.COMPLIANT, AIStatus.OK, corrected, False) is True


def test_regression_case_phrases_are_locatable():
    for case in (NON_COMPLIANT, COMPLIANT, PARTIALLY_COMPLIANT):
        for phrase in case.must_flag + case.must_not_flag:
            assert locate(phrase, case.content) is not None, (case.name, phrase)
