"""Tests for the deterministic rule engine and the 3 LumaCare test cases."""

import pytest

from app.enums import FindingCategory, FindingType, OverallStatus, Severity
from app.mappers import brand_to_knowledge
from app.models import BrandProfile
from app.services.analyzer import analyze_content
from app.services.rule_engine import run_rule_engine
from tests.fixtures.lumacare_cases import COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT


def test_test1_non_compliant_rule_engine(seeded_db):
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    findings, positives = run_rule_engine(NON_COMPLIANT.content, knowledge)

    # Must detect prohibited terminology or guarantee
    violation_types = [f.finding_type for f in findings]
    assert FindingType.CONFIRMED_RULE_VIOLATION in violation_types

    # Must flag prohibited term
    term_finding = next((f for f in findings if f.category == FindingCategory.TERMINOLOGY), None)
    assert term_finding is not None
    assert "guaranteed acne removal" in term_finding.explanation.lower() or "prohibited" in term_finding.explanation.lower()

    # Must flag timeframe
    timeframe_finding = next((f for f in findings if f.category == FindingCategory.TIMEFRAME), None)
    assert timeframe_finding is not None
    assert "2 days" in timeframe_finding.original_text

    # Analyzer must mark it NON_COMPLIANT
    result = analyze_content(NON_COMPLIANT.content, knowledge)
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert result.requires_human_review is True


def test_test2_compliant_rule_engine(seeded_db):
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    findings, positives = run_rule_engine(COMPLIANT.content, knowledge)

    # Must NOT produce confirmed violations
    assert not any(f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION for f in findings)
    # Must recognise positive observations (preferred terminology)
    assert any("supports clearer-looking skin" in p for p in positives)

    # When AI is disabled, status policy gives NEEDS_REVIEW because AI didn't run,
    # but with no findings it would be COMPLIANT once AI completes.
    # Let's verify findings list has no blockers:
    blockers = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
    assert len(blockers) == 0


def test_test3_partially_compliant_rule_engine(seeded_db):
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    findings, positives = run_rule_engine(PARTIALLY_COMPLIANT.content, knowledge)

    # Should flag the unapproved timeframe "within 7 days"
    timeframe_finding = next((f for f in findings if f.category == FindingCategory.TIMEFRAME), None)
    assert timeframe_finding is not None
    assert "7 days" in timeframe_finding.original_text

    # Preferred term should still be recognised in positives
    assert any("supports clearer-looking skin" in p for p in positives)

    # Overall status should be NEEDS_REVIEW
    result = analyze_content(PARTIALLY_COMPLIANT.content, knowledge)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert result.requires_human_review is True


def test_arbitrary_case_a_insufficient_context_single_word(seeded_db):
    """Case A: 'hellloooooooo' -> Needs review or insufficient context, not automatically compliant."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    findings, _ = run_rule_engine("hellloooooooo", knowledge)
    assert len(findings) == 1
    assert findings[0].category == FindingCategory.OTHER
    assert findings[0].finding_type == FindingType.POTENTIAL_ISSUE
    assert "insufficient" in findings[0].explanation.lower()

    result = analyze_content("hellloooooooo", knowledge)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert result.requires_human_review is True
    assert "insufficient" in result.summary.lower()


def test_arbitrary_case_b_guarantee_48_hours(seeded_db):
    """Case B: 'LumaCare guarantees acne removal in 48 hours.' -> Non-compliant."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    text = "LumaCare guarantees acne removal in 48 hours."
    findings, _ = run_rule_engine(text, knowledge)

    # Must flag prohibited term or guarantee
    assert any(f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION for f in findings)
    # Must flag timeframe
    assert any(f.category == FindingCategory.TIMEFRAME and "48 hours" in f.original_text for f in findings)

    result = analyze_content(text, knowledge)
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert result.requires_human_review is True


def test_arbitrary_case_c_compliant_substantive(seeded_db):
    """Case C: 'LumaCare supports clearer-looking skin.' -> Compliant."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    text = "LumaCare supports clearer-looking skin."
    findings, positives = run_rule_engine(text, knowledge)

    # Must have no violations
    assert len(findings) == 0
    # Must have positive observation for preferred terminology
    assert any("supports clearer-looking skin" in p for p in positives)


def test_arbitrary_case_d_reduces_acne_seven_days(seeded_db):
    """Case D: 'Our cream reduces acne within seven days.' -> Needs review."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    text = "Our cream reduces acne within seven days."
    findings, _ = run_rule_engine(text, knowledge)

    # Must flag timeframe with spelled-out number 'seven days'
    assert any(f.category == FindingCategory.TIMEFRAME and "seven days" in f.original_text.lower() for f in findings)
    # Must flag unapproved acne claim
    assert any("acne" in f.original_text.lower() for f in findings)

    result = analyze_content(text, knowledge)
    assert result.overall_status in (OverallStatus.NEEDS_REVIEW, OverallStatus.NON_COMPLIANT)
    assert result.requires_human_review is True


def test_arbitrary_case_e_generic_greeting_insufficient_context(seeded_db):
    """Case E: 'Have a beautiful day!' -> Insufficient context or needs review."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    findings, _ = run_rule_engine("Have a beautiful day!", knowledge)
    assert len(findings) == 1
    assert findings[0].category == FindingCategory.OTHER
    assert findings[0].finding_type == FindingType.POTENTIAL_ISSUE
    assert "insufficient" in findings[0].explanation.lower()

    result = analyze_content("Have a beautiful day!", knowledge)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert result.requires_human_review is True
    assert "insufficient" in result.summary.lower()
