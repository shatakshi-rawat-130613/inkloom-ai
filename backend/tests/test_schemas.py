"""Request validation and AI output contract tests."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas import (
    MAX_BODY_CHARS,
    AIAnalysisOutput,
    ReviewCreate,
    SubmissionCreate,
    VersionCreate,
)


def _valid_submission(**overrides):
    data = {"brand_id": str(uuid.uuid4()), "title": "Launch post", "content_type": "social_post", "body": "Hello"}
    data.update(overrides)
    return data


def test_submission_create_defaults_author():
    assert SubmissionCreate(**_valid_submission()).author_name == "Demo Editor"


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},
        {"title": "   "},
        {"body": ""},
        {"body": "x" * (MAX_BODY_CHARS + 1)},
        {"content_type": "tweet"},
        {"brand_id": "not-a-uuid"},
        {"unexpected": "field"},
    ],
)
def test_submission_create_rejects_invalid_input(overrides):
    with pytest.raises(ValidationError):
        SubmissionCreate(**_valid_submission(**overrides))


def test_version_create_limits():
    VersionCreate(body="ok", change_note="Removed guarantee")
    with pytest.raises(ValidationError):
        VersionCreate(body="ok", change_note="x" * 501)


def test_review_requires_comments_unless_approved():
    ReviewCreate(decision="approved", reviewer_name="Demo Reviewer")
    for decision in ("rejected", "revisions_requested"):
        with pytest.raises(ValidationError):
            ReviewCreate(decision=decision, reviewer_name="Demo Reviewer", comments="  ")
        ReviewCreate(decision=decision, reviewer_name="Demo Reviewer", comments="Please remove the timeframe.")


def test_ai_output_parses_valid_payload():
    out = AIAnalysisOutput.model_validate_json(
        """{"summary": "s", "positive_observations": ["Friendly tone"], "requires_human_review": true,
            "findings": [{"category": "timeframe", "severity": "high", "finding_type": "unsupported_claim",
                          "original_text": "within 7 days", "guideline_id": "GUIDE-003",
                          "approved_fact_id": "FACT-002", "explanation": "e", "suggestion": null, "confidence": 0.8}]}"""
    )
    assert out.findings[0].approved_fact_id == "FACT-002"


@pytest.mark.parametrize(
    "bad",
    [
        '{"summary": "s", "findings": [], "positive_observations": []}',  # missing field
        '{"summary": "s", "findings": [{"category": "x"}], "positive_observations": [], "requires_human_review": false}',
        '{"summary": "s", "findings": [], "positive_observations": [], "requires_human_review": false, '
        '"overall_status": "compliant", "findings": [{"category": "tone", "severity": "Severe", "finding_type": "recommendation", '
        '"original_text": "", "explanation": "e", "confidence": 0.5}]}',
        "not json",
    ],
)
def test_ai_output_rejects_invalid_payloads(bad):
    with pytest.raises(ValidationError):
        AIAnalysisOutput.model_validate_json(bad)


def test_ai_output_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        AIAnalysisOutput.model_validate(
            {"summary": "s", "positive_observations": [], "requires_human_review": False,
             "findings": [{"category": "tone", "severity": "low", "finding_type": "recommendation",
                           "original_text": "", "explanation": "e", "confidence": 1.5}]}
        )


def test_ai_output_json_schema_is_generatable():
    schema = AIAnalysisOutput.model_json_schema()
    assert "findings" in schema["properties"]
    assert "overall_status" not in schema["properties"]
