"""Schema, relationship and seed tests for the shared database models."""

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError, StatementError

from app.enums import AIStatus, ContentType, FindingCategory, FindingSource, FindingType, OverallStatus, ReviewDecision, Severity
from app.mappers import brand_to_detail, brand_to_knowledge
from app.models import (
    AnalysisRun,
    ApprovedFact,
    ApprovedTerm,
    BrandGuideline,
    BrandProfile,
    ComplianceIssue,
    ContentSubmission,
    ContentVersion,
    HumanReview,
    User,
)
from app.seed import seed_demo_data

EXPECTED_TABLES = {
    "organisations",
    "users",
    "brand_profiles",
    "brand_guidelines",
    "approved_facts",
    "approved_terms",
    "brand_assets",
    "document_extractions",
    "content_submissions",
    "content_versions",
    "analysis_runs",
    "compliance_issues",
    "human_reviews",
    "audit_logs",
}


def test_all_tables_created(engine):
    table_names = set(inspect(engine).get_table_names())
    # May or may not include alembic_version depending on migration runner
    table_names.discard("alembic_version")
    assert table_names == EXPECTED_TABLES


def test_seed_matches_brief_exactly(seeded_db):
    brand = seeded_db.scalar(select(BrandProfile).where(BrandProfile.slug == "lumacare"))
    knowledge = brand_to_knowledge(brand)
    assert {g.id: g.text for g in knowledge.guidelines} == {
        "GUIDE-001": "Do not promise guaranteed medical or skincare outcomes.",
        "GUIDE-002": "Use friendly, reassuring and realistic messaging.",
        "GUIDE-003": "Claims must be consistent with approved product information.",
    }
    assert {f.id: f.statement for f in knowledge.facts} == {
        "FACT-001": "The product is designed to support clearer-looking skin.",
        "FACT-002": "No guaranteed acne-removal timeframe has been approved.",
    }
    (term,) = knowledge.terms
    assert term.id == "TERM-001"
    assert term.preferred_term == "supports clearer-looking skin"
    assert term.prohibited_term == "guaranteed acne removal"
    assert term.related_guideline_id == "GUIDE-001"


def test_seed_is_idempotent(seeded_db):
    seed_demo_data(seeded_db)
    seed_demo_data(seeded_db)
    from app.models import BrandAsset
    for model, expected in [(BrandProfile, 1), (BrandGuideline, 3), (ApprovedFact, 2), (ApprovedTerm, 1), (User, 3), (BrandAsset, 3)]:
        assert seeded_db.scalar(select(func.count()).select_from(model)) == expected


def test_brand_detail_exposes_codes_not_uuids(seeded_db):
    brand = seeded_db.scalar(select(BrandProfile))
    detail = brand_to_detail(brand)
    assert detail.is_demo is True
    assert [g.id for g in detail.guidelines] == ["GUIDE-001", "GUIDE-002", "GUIDE-003"]


def _submission_with_version(db, brand, body="Hello"):
    sub = ContentSubmission(brand_id=brand.id, title="T", content_type=ContentType.SOCIAL_POST, author_name="Demo Editor")
    db.add(sub)
    db.flush()
    v = ContentVersion(submission_id=sub.id, version_number=1, body=body)
    db.add(v)
    db.flush()
    return sub, v


def _run(db, sub, version, status=OverallStatus.COMPLIANT):
    run = AnalysisRun(
        submission_id=sub.id,
        version_id=version.id,
        overall_status=status,
        summary="s",
        positive_observations=[],
        requires_human_review=False,
        ai_status=AIStatus.OK,
        rule_engine_version="1",
        knowledge_snapshot={},
    )
    db.add(run)
    db.flush()
    return run


def test_history_is_preserved_across_versions_runs_and_reviews(seeded_db):
    db = seeded_db
    brand = db.scalar(select(BrandProfile))
    sub, v1 = _submission_with_version(db, brand, "first")
    run1 = _run(db, sub, v1, OverallStatus.NON_COMPLIANT)
    v2 = ContentVersion(submission_id=sub.id, version_number=2, body="second")
    db.add(v2)
    db.flush()
    run2 = _run(db, sub, v2)
    run2b = _run(db, sub, v2)  # re-analysis of the same version keeps both
    db.add(HumanReview(submission_id=sub.id, version_id=v2.id, analysis_run_id=run2b.id, reviewer_name="Demo Reviewer", decision=ReviewDecision.APPROVED))
    db.commit()
    db.expire_all()

    sub = db.get(ContentSubmission, sub.id)
    assert [v.body for v in sub.versions] == ["first", "second"]
    assert {r.id for r in sub.analysis_runs} == {run1.id, run2.id, run2b.id}
    assert db.get(AnalysisRun, run1.id).version.body == "first"
    assert len(db.get(ContentVersion, v2.id).analysis_runs) == 2
    assert sub.reviews[0].version_id == v2.id


def test_version_numbers_unique_per_submission(seeded_db):
    brand = seeded_db.scalar(select(BrandProfile))
    sub, _ = _submission_with_version(seeded_db, brand)
    seeded_db.add(ContentVersion(submission_id=sub.id, version_number=1, body="dup"))
    with pytest.raises(IntegrityError):
        seeded_db.flush()


def test_finding_references_must_be_real_rows(seeded_db):
    import uuid

    brand = seeded_db.scalar(select(BrandProfile))
    sub, v = _submission_with_version(seeded_db, brand)
    run = _run(seeded_db, sub, v)
    seeded_db.add(
        ComplianceIssue(
            analysis_run_id=run.id, position=0, source=FindingSource.AI, category=FindingCategory.OTHER,
            severity=Severity.LOW, finding_type=FindingType.POTENTIAL_ISSUE, original_text="x",
            explanation="e", confidence=0.5, guideline_id=uuid.uuid4(),
        )
    )
    with pytest.raises(IntegrityError):
        seeded_db.flush()


def test_enum_columns_reject_unknown_values(seeded_db):
    brand = seeded_db.scalar(select(BrandProfile))
    seeded_db.add(ContentSubmission(brand_id=brand.id, title="T", content_type="tweet", author_name="x"))
    with pytest.raises((StatementError, LookupError)):
        seeded_db.flush()


def test_history_cannot_be_deleted_through_parent(seeded_db):
    brand = seeded_db.scalar(select(BrandProfile))
    sub, v = _submission_with_version(seeded_db, brand)
    _run(seeded_db, sub, v)
    seeded_db.commit()
    from sqlalchemy import delete

    with pytest.raises(IntegrityError):
        seeded_db.execute(delete(ContentVersion).where(ContentVersion.id == v.id))
        seeded_db.flush()
