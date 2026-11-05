"""Regression tests for Brand Relevance Detection and Cross-Industry Validation.

Verifies the 8 required test scenarios from the specification:
1. Valid LumaCare skincare copy -> COMPLIANT
2. Guaranteed acne-removal claim -> NON_COMPLIANT
3. Unsupported seven-day acne-reduction claim -> NEEDS_REVIEW
4. Detailed Harvest & Hearth food-brand description -> NEEDS_REVIEW + UNRELATED_TO_BRAND
   - No LumaCare confirmed violations produced
   - No irrelevant skincare corrections generated
   - No fabricated evidence references appear
   - Final status is not NON_COMPLIANT
   - Final status is not COMPLIANT
   - Unrelated classification clearly visible
   - Human review remains available
   - Submission and analysis history persist
5. 'hellloooooooo' -> NEEDS_REVIEW due to insufficient context
6. 'Have a beautiful day!' -> NEEDS_REVIEW due to insufficient context
7. Short valid LumaCare slogan with relevant submission context -> Not classified as unrelated (RELEVANT)
8. Skincare copy containing a potentially unsupported claim -> Assessed against LumaCare knowledge, not classified as unrelated
"""

import pytest
from uuid import UUID

from app.enums import (
    ContentType,
    FindingCategory,
    FindingType,
    OverallStatus,
    ReviewDecision,
    Severity,
    SubmissionAction,
    SubmissionStatus,
)
from app.mappers import brand_to_knowledge
from app.models import BrandProfile
from app.schemas import ReviewCreate, ReviewRequestCreate, SubmissionCreate
from app.services.analyzer import analyze_content
from app.services.relevance import BrandRelevance, assess_brand_relevance
from app.services.submission_service import (
    analyze_submission,
    create_submission,
    get_submission_detail,
    record_review,
    request_review,
)
from tests.fixtures.harvest_and_hearth import HARVEST_AND_HEARTH_TEXT
from tests.fixtures.lumacare_cases import COMPLIANT, NON_COMPLIANT, PARTIALLY_COMPLIANT


def test_scenario_1_valid_lumacare_skincare_copy(seeded_db):
    """Test 1: Valid LumaCare skincare copy -> COMPLIANT."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    relevance = assess_brand_relevance(COMPLIANT.content, knowledge, title=COMPLIANT.name)
    assert relevance.status == BrandRelevance.RELEVANT

    result = analyze_content(COMPLIANT.content, knowledge, title=COMPLIANT.name)
    assert not any(f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION for f in result.findings)
    assert not any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in result.findings)


def test_scenario_2_guaranteed_acne_removal_claim(seeded_db):
    """Test 2: Guaranteed acne-removal claim -> NON_COMPLIANT."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    relevance = assess_brand_relevance(NON_COMPLIANT.content, knowledge, title=NON_COMPLIANT.name)
    assert relevance.status == BrandRelevance.RELEVANT

    result = analyze_content(NON_COMPLIANT.content, knowledge, title=NON_COMPLIANT.name)
    assert result.overall_status == OverallStatus.NON_COMPLIANT
    assert any(f.finding_type == FindingType.CONFIRMED_RULE_VIOLATION for f in result.findings)
    assert result.requires_human_review is True


def test_scenario_3_unsupported_seven_day_acne_claim(seeded_db):
    """Test 3: Unsupported seven-day acne-reduction claim -> NEEDS_REVIEW."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    relevance = assess_brand_relevance(PARTIALLY_COMPLIANT.content, knowledge, title=PARTIALLY_COMPLIANT.name)
    assert relevance.status == BrandRelevance.RELEVANT

    result = analyze_content(PARTIALLY_COMPLIANT.content, knowledge, title=PARTIALLY_COMPLIANT.name)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert any(f.category == FindingCategory.TIMEFRAME for f in result.findings)
    assert result.requires_human_review is True


def test_scenario_4_harvest_and_hearth_food_brand_unrelated(seeded_db):
    """Test 4: Detailed Harvest & Hearth food-brand description -> NEEDS_REVIEW + UNRELATED_TO_BRAND.

    Verifications:
    - No LumaCare confirmed violations are produced.
    - No irrelevant skincare corrections are generated.
    - No fabricated evidence references appear.
    - Final status is not NON_COMPLIANT.
    - Final status is not COMPLIANT.
    - The unrelated classification is clearly visible.
    - Human review remains available.
    - The submission and analysis history persist.
    """
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    # 1. Relevance assessment
    relevance = assess_brand_relevance(
        HARVEST_AND_HEARTH_TEXT,
        knowledge,
        title="Harvest & Hearth Brand Guidelines",
        content_type="product_description",
    )
    assert relevance.status == BrandRelevance.UNRELATED
    assert relevance.reason_code == "UNRELATED_TO_BRAND"
    assert "unrelated to LumaCare" in relevance.explanation

    # 2. Complete analysis result
    result = analyze_content(
        HARVEST_AND_HEARTH_TEXT,
        knowledge,
        title="Harvest & Hearth Brand Guidelines",
        content_type="product_description",
    )

    # Status verifications
    assert result.overall_status != OverallStatus.NON_COMPLIANT, "Must not be classified as NON_COMPLIANT"
    assert result.overall_status != OverallStatus.COMPLIANT, "Must not be classified as COMPLIANT"
    assert result.overall_status == OverallStatus.NEEDS_REVIEW

    # Summary verification
    assert result.summary.startswith("UNRELATED TO ACTIVE BRAND:"), "Summary must clearly state unrelated to brand"
    assert "LumaCare" in result.summary

    # Finding checks
    assert len(result.findings) == 1
    unrelated_finding = result.findings[0]

    # No LumaCare confirmed violations
    assert unrelated_finding.finding_type != FindingType.CONFIRMED_RULE_VIOLATION
    assert unrelated_finding.finding_type == FindingType.POTENTIAL_ISSUE

    # No fabricated guideline/fact references
    assert unrelated_finding.guideline_id is None
    assert unrelated_finding.approved_fact_id is None
    assert unrelated_finding.approved_term_id is None

    # No irrelevant skincare corrections
    assert "skincare" not in unrelated_finding.suggestion.lower() or "submit content relevant to lumacare" in unrelated_finding.suggestion.lower()
    assert "clearer-looking skin" not in (unrelated_finding.suggestion or "").lower()

    # Clear reason code in reference_note
    assert unrelated_finding.reference_note == "Reason code: UNRELATED_TO_BRAND"

    # Human review must be required
    assert result.requires_human_review is True

    # 3. Full persistence and workflow test via submission service
    sub = create_submission(
        seeded_db,
        SubmissionCreate(
            brand_id=brand.id,
            title="Harvest & Hearth Brand Overview",
            content_type=ContentType.PRODUCT_DESCRIPTION,
            body=HARVEST_AND_HEARTH_TEXT,
            author_name="Demo Editor",
        ),
    )
    assert sub.id is not None

    # Run analysis through service layer
    run_schema = analyze_submission(seeded_db, sub.id)
    assert run_schema.overall_status == OverallStatus.NEEDS_REVIEW
    assert run_schema.summary.startswith("UNRELATED TO ACTIVE BRAND:")
    assert len(run_schema.findings) == 1
    assert run_schema.findings[0].reference_note == "Reason code: UNRELATED_TO_BRAND"

    # Verify submission detail and actions
    detail = get_submission_detail(seeded_db, sub.id)
    assert detail.status == SubmissionStatus.ANALYZED
    assert detail.latest_overall_status == OverallStatus.NEEDS_REVIEW
    assert SubmissionAction.REQUEST_REVIEW in detail.allowed_actions

    # Test human review availability
    request_review(seeded_db, sub.id, requested_by="Demo Editor", note="Review unrelated content")
    detail_after_req = get_submission_detail(seeded_db, sub.id)
    assert detail_after_req.status == SubmissionStatus.IN_REVIEW
    assert SubmissionAction.REVIEW in detail_after_req.allowed_actions

    # Complete human review
    record_review(
        seeded_db,
        sub.id,
        decision=ReviewDecision.REJECTED,
        reviewer_name="Brand Lead",
        comments="Content describes Harvest & Hearth food brand, which does not belong to LumaCare workspace.",
    )
    detail_final = get_submission_detail(seeded_db, sub.id)
    assert detail_final.status == SubmissionStatus.REJECTED
    assert len(detail_final.reviews) == 1
    assert len(detail_final.analysis_runs) == 1


def test_scenario_5_single_word_insufficient_context(seeded_db):
    """Test 5: 'hellloooooooo' -> NEEDS_REVIEW due to insufficient context."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    relevance = assess_brand_relevance("hellloooooooo", knowledge)
    assert relevance.status == BrandRelevance.INSUFFICIENT_CONTEXT

    result = analyze_content("hellloooooooo", knowledge)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert result.requires_human_review is True
    assert "insufficient" in result.summary.lower()
    assert len(result.findings) == 1
    assert result.findings[0].category == FindingCategory.OTHER
    assert "insufficient" in result.findings[0].explanation.lower()


def test_scenario_6_generic_greeting_insufficient_context(seeded_db):
    """Test 6: 'Have a beautiful day!' -> NEEDS_REVIEW due to insufficient context."""
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    relevance = assess_brand_relevance("Have a beautiful day!", knowledge)
    assert relevance.status == BrandRelevance.INSUFFICIENT_CONTEXT

    result = analyze_content("Have a beautiful day!", knowledge)
    assert result.overall_status == OverallStatus.NEEDS_REVIEW
    assert result.requires_human_review is True
    assert "insufficient" in result.summary.lower()


def test_scenario_7_short_valid_lumacare_slogan_not_unrelated(seeded_db):
    """Test 7: Short valid LumaCare slogan with relevant submission context

    Must not automatically be classified as unrelated.
    """
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    slogan = "LumaCare: Gentle, confident skincare."
    relevance = assess_brand_relevance(slogan, knowledge, title="Brand Tagline")
    assert relevance.status == BrandRelevance.RELEVANT, "Slogan mentioning brand name and domain must be RELEVANT"

    result = analyze_content(slogan, knowledge, title="Brand Tagline")
    assert not result.summary.startswith("UNRELATED TO ACTIVE BRAND")
    assert not any(f.reference_note == "Reason code: UNRELATED_TO_BRAND" for f in result.findings)

    # Test short copy with LumaCare title context
    short_copy = "Gentle, confident skincare for every day."
    relevance_context = assess_brand_relevance(short_copy, knowledge, title="LumaCare Daily Routine")
    assert relevance_context.status == BrandRelevance.RELEVANT


def test_scenario_8_skincare_copy_unsupported_claim_not_unrelated(seeded_db):
    """Test 8: Skincare copy containing a potentially unsupported claim

    Must be assessed against LumaCare knowledge, not classified as unrelated.
    """
    brand = seeded_db.query(BrandProfile).filter_by(slug="lumacare").one()
    knowledge = brand_to_knowledge(brand)

    # Copy does not mention LumaCare, but discusses skincare domain (cream, acne, seven days)
    skincare_copy = "Our clarifying cream reduces acne and clears blemishes within seven days."

    relevance = assess_brand_relevance(skincare_copy, knowledge, title="Product Announcement")
    assert relevance.status == BrandRelevance.RELEVANT, "Skincare copy must be identified as RELEVANT domain"

    result = analyze_content(skincare_copy, knowledge, title="Product Announcement")
    assert not result.summary.startswith("UNRELATED TO ACTIVE BRAND")
    assert not any(f.reference_note == "Reason code: UNRELATED_TO_BRAND" for f in result.findings)

    # It must be evaluated against LumaCare knowledge:
    # flags unapproved acne claim and timeframe
    assert any(f.category == FindingCategory.TIMEFRAME for f in result.findings)
    assert result.overall_status in (OverallStatus.NEEDS_REVIEW, OverallStatus.NON_COMPLIANT)
