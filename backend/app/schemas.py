"""Pydantic schemas: API request/response contracts and the AI output contract.

Centrally controlled contract file. Mirrored field-for-field in
frontend/src/api/types.ts (checked by tests/test_contract_parity.py).

Identifier convention
- Submissions, versions, runs, findings and reviews are identified by UUID.
- Brand knowledge items are identified by their stable code (GUIDE-001,
  FACT-001, TERM-001). ``guideline_id`` and ``approved_fact_id`` on a finding
  always hold these codes, never internal UUIDs.
"""

from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import (
    AIStatus,
    ContentType,
    FindingCategory,
    FindingSource,
    FindingType,
    OverallStatus,
    ReviewDecision,
    Severity,
    SubmissionAction,
    SubmissionStatus,
    UserRole,
)

# Hard upper bound enforced at the schema level. Settings.max_content_chars may
# lower it at runtime but never raise it.
MAX_BODY_CHARS = 10_000


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ==========================================================================
# Errors
# ==========================================================================


class ErrorBody(BaseModel):
    code: str = Field(description="Machine-readable error code, see docs/api-contract.md")
    message: str = Field(description="Safe, user-facing message")
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


# ==========================================================================
# Brand knowledge
# ==========================================================================


class Guideline(_Out):
    id: str = Field(description="Stable code, e.g. GUIDE-001")
    title: str
    text: str
    category: FindingCategory
    default_severity: Severity


class Fact(_Out):
    id: str = Field(description="Stable code, e.g. FACT-001")
    statement: str
    source: str | None


class Term(_Out):
    id: str = Field(description="Stable code, e.g. TERM-001")
    preferred_term: str | None
    prohibited_term: str | None
    notes: str | None
    related_guideline_id: str | None


class BrandSummary(_Out):
    id: UUID
    slug: str
    name: str
    industry: str
    description: str
    is_demo: bool
    organisation_id: UUID | None = None


class BrandDetail(BrandSummary):
    voice_summary: str
    guidelines: list[Guideline]
    facts: list[Fact]
    terms: list[Term]


class BrandKnowledge(BaseModel):
    """Exact knowledge supplied to the rule engine and Gemini for one run.
    Stored on AnalysisRun.knowledge_snapshot."""

    brand_name: str
    guidelines: list[Guideline]
    facts: list[Fact]
    terms: list[Term]

    def guideline_codes(self) -> set[str]:
        return {g.id for g in self.guidelines}

    def fact_codes(self) -> set[str]:
        return {f.id for f in self.facts}

    def term_codes(self) -> set[str]:
        return {t.id for t in self.terms}


# ==========================================================================
# Findings and analysis runs
# ==========================================================================


class Finding(_Out):
    id: UUID
    position: int
    source: FindingSource
    category: FindingCategory
    severity: Severity
    finding_type: FindingType
    original_text: str
    start_offset: int | None
    end_offset: int | None
    guideline_id: str | None = Field(description="Verified guideline code or null")
    approved_fact_id: str | None = Field(description="Verified fact code or null")
    approved_term_id: str | None = Field(description="Verified term code or null")
    evidence: str | None = Field(description="Verbatim text of the cited guideline/fact, built server-side")
    explanation: str
    suggestion: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    reference_note: str | None = Field(description="Set when the validator removed or downgraded a reference")


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class AnalysisRunSummary(_Out):
    id: UUID
    version_id: UUID
    version_number: int
    overall_status: OverallStatus
    requires_human_review: bool
    ai_status: AIStatus
    finding_count: int
    severity_counts: SeverityCounts
    created_at: datetime


class AnalysisRun(AnalysisRunSummary):
    submission_id: UUID
    summary: str
    positive_observations: list[str]
    model_name: str | None
    rule_engine_version: str
    duration_ms: int | None
    findings: list[Finding]


# ==========================================================================
# Submissions, versions, reviews, audit
# ==========================================================================


class ContentVersion(_Out):
    id: UUID
    version_number: int
    body: str
    change_note: str | None
    created_at: datetime
    analysis_run_ids: list[UUID]


class HumanReview(_Out):
    id: UUID
    version_id: UUID
    version_number: int
    analysis_run_id: UUID | None
    reviewer_name: str
    decision: ReviewDecision
    comments: str | None
    created_at: datetime


class AuditLogEntry(_Out):
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_name: str
    details: dict[str, Any]
    created_at: datetime


class SubmissionListItem(_Out):
    id: UUID
    brand_id: UUID
    brand_name: str
    title: str
    content_type: ContentType
    status: SubmissionStatus
    current_version_number: int
    latest_overall_status: OverallStatus | None
    author_name: str
    created_at: datetime
    updated_at: datetime


class SubmissionDetail(SubmissionListItem):
    versions: list[ContentVersion]
    analysis_runs: list[AnalysisRunSummary]
    latest_analysis: AnalysisRun | None = Field(description="Most recent run for the current version, if any")
    reviews: list[HumanReview]
    allowed_actions: list[SubmissionAction]


# ==========================================================================
# Requests
# ==========================================================================


class SubmissionCreate(_Strict):
    brand_id: UUID
    title: str = Field(min_length=1, max_length=200)
    content_type: ContentType
    body: str = Field(min_length=1, max_length=MAX_BODY_CHARS)
    author_name: str = Field(default="Demo Editor", min_length=1, max_length=100)


class VersionCreate(_Strict):
    body: str = Field(min_length=1, max_length=MAX_BODY_CHARS)
    change_note: str | None = Field(default=None, max_length=500)


class ReviewRequestCreate(_Strict):
    requested_by: str = Field(default="Demo Editor", min_length=1, max_length=100)
    note: str | None = Field(default=None, max_length=1000)


class ReviewCreate(_Strict):
    decision: ReviewDecision
    reviewer_name: str = Field(min_length=1, max_length=100)
    comments: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _comments_required_for_negative_decisions(self) -> Self:
        if self.decision != ReviewDecision.APPROVED and not (self.comments and self.comments.strip()):
            raise ValueError("Comments are required when rejecting or requesting revisions.")
        return self


class HealthResponse(BaseModel):
    status: str
    database: str
    ai: AIStatus


class UserResponse(_Out):
    id: UUID
    organisation_id: UUID
    organisation_name: str
    display_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AuthResponse(_Out):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OrganisationLookupResponse(_Out):
    exists: bool
    name: str | None = None
    slug: str | None = None
    message: str | None = None


class UserRegisterRequest(_Strict):
    organisation_name: str = Field(min_length=2, max_length=120)
    display_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(_Strict):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class MemberCreateRequest(_Strict):
    display_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole


class BrandCreateRequest(_Strict):
    name: str = Field(min_length=2, max_length=100)
    industry: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=1000)
    voice_summary: str = Field(min_length=5, max_length=1000)


class BrandUpdateRequest(_Strict):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    industry: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=5, max_length=1000)
    voice_summary: str | None = Field(default=None, min_length=5, max_length=1000)


class GuidelineCreateRequest(_Strict):
    code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=2, max_length=200)
    rule_text: str = Field(min_length=5, max_length=1000)
    category: FindingCategory
    default_severity: Severity


class FactCreateRequest(_Strict):
    code: str = Field(min_length=2, max_length=50)
    statement: str = Field(min_length=5, max_length=1000)
    source: str | None = Field(default=None, max_length=500)


class TermCreateRequest(_Strict):
    code: str = Field(min_length=2, max_length=50)
    preferred_term: str | None = Field(default=None, max_length=200)
    prohibited_term: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=500)
    related_guideline_code: str | None = Field(default=None, max_length=50)


class BrandAssetCreateRequest(_Strict):
    asset_type: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)
    asset_metadata: dict[str, Any]


class BrandAssetResponse(_Out):
    id: UUID
    brand_id: UUID
    asset_type: str
    name: str
    asset_metadata: dict[str, Any]
    is_active: bool
    created_at: datetime


class DocumentExtractionResponse(_Out):
    id: UUID
    submission_id: UUID | None
    file_name: str
    file_type: str
    file_size_bytes: int
    extraction_source: str
    extracted_text: str
    extraction_status: str
    extraction_metadata: dict[str, Any]
    created_at: datetime


# ==========================================================================
# AI contract (Gemini structured output) and internal finding draft
# ==========================================================================


class AIFinding(BaseModel):
    """One finding as returned by Gemini. Untrusted until verified."""

    category: FindingCategory
    severity: Severity
    finding_type: FindingType
    original_text: str = Field(description="Exact quote from the submitted content")
    guideline_id: str | None = Field(default=None, description="Code of a supplied guideline, or null")
    approved_fact_id: str | None = Field(default=None, description="Code of a supplied fact, or null")
    explanation: str
    suggestion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class AIAnalysisOutput(BaseModel):
    """Gemini response_schema. Overall status is NOT taken from the model; it
    is derived deterministically by app.validation.derive_overall_status."""

    summary: str
    findings: list[AIFinding]
    positive_observations: list[str]
    requires_human_review: bool


class FindingDraft(BaseModel):
    """Validated finding ready to persist. Produced by the rule engine directly
    and by app.validation.verify_ai_findings for Gemini output."""

    source: FindingSource
    category: FindingCategory
    severity: Severity
    finding_type: FindingType
    original_text: str
    start_offset: int | None = None
    end_offset: int | None = None
    guideline_id: str | None = None
    approved_fact_id: str | None = None
    approved_term_id: str | None = None
    evidence: str | None = None
    explanation: str
    suggestion: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reference_note: str | None = None

    @field_validator("guideline_id", "approved_fact_id", "approved_term_id")
    @classmethod
    def _upper(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class DocumentExtractResponse(BaseModel):
    file_name: str
    file_type: str
    file_size_bytes: int
    extraction_source: str
    extracted_text: str
    extraction_metadata: dict[str, Any]
    visual_findings: list[FindingDraft] = Field(default_factory=list)
