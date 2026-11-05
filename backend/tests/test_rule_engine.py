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
