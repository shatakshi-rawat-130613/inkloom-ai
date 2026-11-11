"""SQLAlchemy ORM models.

Centrally controlled contract file. Do not change without coordinator approval.
Documented in docs/database-schema.md.

Design notes
- UUID primary keys everywhere. Brand knowledge also carries a stable
  human-readable ``code`` (GUIDE-001, FACT-001, TERM-001) that is unique per
  brand and is the identifier exposed to the API and to Gemini.
- History is append-only: content versions, analysis runs, findings and
  reviews are never updated or deleted by the application. Foreign keys use
  ON DELETE RESTRICT so history cannot be silently removed.
- Enums are stored as VARCHAR with CHECK constraints (native_enum=False) so
  the schema stays portable between PostgreSQL and SQLite tests.
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.enums import (
    AIStatus,
    ContentType,
    FindingCategory,
    FindingSource,
    FindingType,
    OverallStatus,
    ReviewDecision,
    Severity,
    SubmissionStatus,
    UserRole,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=_utcnow, server_default=func.now(), nullable=False)


def _fk(target: str, *, nullable: bool = False, index: bool = True) -> Mapped[Any]:
    return mapped_column(Uuid, ForeignKey(target, ondelete="RESTRICT"), nullable=nullable, index=index)


# --------------------------------------------------------------------------
# Organisation, users, brand knowledge
# --------------------------------------------------------------------------


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    created_at: Mapped[datetime] = _created_at()

    brands: Mapped[list["BrandProfile"]] = relationship(back_populates="organisation")
    users: Mapped[list["User"]] = relationship(back_populates="organisation")


class User(Base):
    """User identities with authentication and role-based permissions."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _pk()
    organisation_id: Mapped[uuid.UUID] = _fk("organisations.id")
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(_enum(UserRole, "user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    organisation: Mapped[Organisation] = relationship(back_populates="users")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id: Mapped[uuid.UUID] = _pk()
    organisation_id: Mapped[uuid.UUID] = _fk("organisations.id")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    voice_summary: Mapped[str] = mapped_column(Text, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, server_default=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship(back_populates="brands")
    guidelines: Mapped[list["BrandGuideline"]] = relationship(
        back_populates="brand", order_by="BrandGuideline.code"
    )
    facts: Mapped[list["ApprovedFact"]] = relationship(back_populates="brand", order_by="ApprovedFact.code")
    terms: Mapped[list["ApprovedTerm"]] = relationship(back_populates="brand", order_by="ApprovedTerm.code")
    assets: Mapped[list["BrandAsset"]] = relationship(back_populates="brand", order_by="BrandAsset.created_at")


class BrandAsset(Base):
    """Visual brand assets: approved logos, color palettes, visual guidelines."""

    __tablename__ = "brand_assets"

    id: Mapped[uuid.UUID] = _pk()
    brand_id: Mapped[uuid.UUID] = _fk("brand_profiles.id")
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "logo", "color_palette", "visual_guideline"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    brand: Mapped[BrandProfile] = relationship(back_populates="assets")


class DocumentExtraction(Base):
    """Uploaded documents and promotional images with extracted text representations."""

    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = _pk()
    submission_id: Mapped[uuid.UUID | None] = _fk("content_submissions.id", nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "pdf", "txt", "image/png", etc.
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extraction_source: Mapped[str] = mapped_column(String(50), nullable=False)  # "document", "ocr", "visual"
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    extraction_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = _created_at()


class BrandGuideline(Base):
    __tablename__ = "brand_guidelines"
    __table_args__ = (UniqueConstraint("brand_id", "code", name="uq_guideline_brand_code"),)

    id: Mapped[uuid.UUID] = _pk()
    brand_id: Mapped[uuid.UUID] = _fk("brand_profiles.id")
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. GUIDE-001
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[FindingCategory] = mapped_column(_enum(FindingCategory, "finding_category"), nullable=False)
    default_severity: Mapped[Severity] = mapped_column(_enum(Severity, "severity"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    brand: Mapped[BrandProfile] = relationship(back_populates="guidelines")


class ApprovedFact(Base):
    __tablename__ = "approved_facts"
    __table_args__ = (UniqueConstraint("brand_id", "code", name="uq_fact_brand_code"),)

    id: Mapped[uuid.UUID] = _pk()
    brand_id: Mapped[uuid.UUID] = _fk("brand_profiles.id")
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. FACT-001
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    brand: Mapped[BrandProfile] = relationship(back_populates="facts")


class ApprovedTerm(Base):
    """One terminology rule: a preferred phrase and/or a prohibited phrase."""

    __tablename__ = "approved_terms"
    __table_args__ = (UniqueConstraint("brand_id", "code", name="uq_term_brand_code"),)

    id: Mapped[uuid.UUID] = _pk()
    brand_id: Mapped[uuid.UUID] = _fk("brand_profiles.id")
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. TERM-001
    preferred_term: Mapped[str | None] = mapped_column(String(300))
    prohibited_term: Mapped[str | None] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    related_guideline_id: Mapped[uuid.UUID | None] = _fk("brand_guidelines.id", nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = _created_at()

    brand: Mapped[BrandProfile] = relationship(back_populates="terms")
    related_guideline: Mapped[BrandGuideline | None] = relationship()


# --------------------------------------------------------------------------
# Content, versions, analysis, review
# --------------------------------------------------------------------------


class ContentSubmission(Base):
    __tablename__ = "content_submissions"
    __table_args__ = (Index("ix_submissions_brand_updated", "brand_id", "updated_at"),)

    id: Mapped[uuid.UUID] = _pk()
    brand_id: Mapped[uuid.UUID] = _fk("brand_profiles.id", index=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(_enum(ContentType, "content_type"), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        _enum(SubmissionStatus, "submission_status"), nullable=False, default=SubmissionStatus.DRAFT, index=True
    )
    current_version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, server_default=func.now(), nullable=False
    )

    brand: Mapped[BrandProfile] = relationship()
    versions: Mapped[list["ContentVersion"]] = relationship(
        back_populates="submission", order_by="ContentVersion.version_number"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="submission", order_by="AnalysisRun.created_at"
    )
    reviews: Mapped[list["HumanReview"]] = relationship(
        back_populates="submission", order_by="HumanReview.created_at"
    )


class ContentVersion(Base):
    """Immutable snapshot of submission text. Editing creates a new version."""

    __tablename__ = "content_versions"
    __table_args__ = (UniqueConstraint("submission_id", "version_number", name="uq_version_submission_number"),)

    id: Mapped[uuid.UUID] = _pk()
    submission_id: Mapped[uuid.UUID] = _fk("content_submissions.id")
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = _created_at()

    submission: Mapped[ContentSubmission] = relationship(back_populates="versions")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        back_populates="version", order_by="AnalysisRun.created_at"
    )


class AnalysisRun(Base):
    """One analysis of one exact content version. Never overwritten."""

    __tablename__ = "analysis_runs"
    __table_args__ = (Index("ix_runs_submission_created", "submission_id", "created_at"),)

    id: Mapped[uuid.UUID] = _pk()
    submission_id: Mapped[uuid.UUID] = _fk("content_submissions.id", index=False)
    version_id: Mapped[uuid.UUID] = _fk("content_versions.id")
    overall_status: Mapped[OverallStatus] = mapped_column(_enum(OverallStatus, "overall_status"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    positive_observations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ai_status: Mapped[AIStatus] = mapped_column(_enum(AIStatus, "ai_status"), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(100))
    rule_engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    # Exact brand knowledge supplied to the analysis, for traceability even if
    # guidelines change later. Shape: schemas.BrandKnowledge.
    knowledge_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created_at()

    submission: Mapped[ContentSubmission] = relationship(back_populates="analysis_runs")
    version: Mapped[ContentVersion] = relationship(back_populates="analysis_runs")
    issues: Mapped[list["ComplianceIssue"]] = relationship(
        back_populates="analysis_run", order_by="ComplianceIssue.position"
    )


class ComplianceIssue(Base):
    """A single finding. Guideline and fact references are real foreign keys,
    so a fabricated reference can never be persisted."""

    __tablename__ = "compliance_issues"

    id: Mapped[uuid.UUID] = _pk()
    analysis_run_id: Mapped[uuid.UUID] = _fk("analysis_runs.id")
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[FindingSource] = mapped_column(_enum(FindingSource, "finding_source"), nullable=False)
    category: Mapped[FindingCategory] = mapped_column(_enum(FindingCategory, "finding_category"), nullable=False)
    severity: Mapped[Severity] = mapped_column(_enum(Severity, "severity"), nullable=False)
    finding_type: Mapped[FindingType] = mapped_column(_enum(FindingType, "finding_type"), nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_offset: Mapped[int | None] = mapped_column(Integer)
    end_offset: Mapped[int | None] = mapped_column(Integer)
    guideline_id: Mapped[uuid.UUID | None] = _fk("brand_guidelines.id", nullable=True, index=False)
    approved_fact_id: Mapped[uuid.UUID | None] = _fk("approved_facts.id", nullable=True, index=False)
    approved_term_id: Mapped[uuid.UUID | None] = _fk("approved_terms.id", nullable=True, index=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    # Set when the validator removed or downgraded something, e.g. an unknown
    # guideline code returned by the model. Shown to reviewers.
    reference_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

    analysis_run: Mapped[AnalysisRun] = relationship(back_populates="issues")
    guideline: Mapped[BrandGuideline | None] = relationship()
    approved_fact: Mapped[ApprovedFact | None] = relationship()
    approved_term: Mapped[ApprovedTerm | None] = relationship()


class HumanReview(Base):
    """Reviewer decision on a specific content version. Append-only."""

    __tablename__ = "human_reviews"
    __table_args__ = (Index("ix_reviews_submission_created", "submission_id", "created_at"),)

    id: Mapped[uuid.UUID] = _pk()
    submission_id: Mapped[uuid.UUID] = _fk("content_submissions.id", index=False)
    version_id: Mapped[uuid.UUID] = _fk("content_versions.id")
    analysis_run_id: Mapped[uuid.UUID | None] = _fk("analysis_runs.id", nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = _fk("users.id", nullable=True, index=False)
    reviewer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(_enum(ReviewDecision, "review_decision"), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

    submission: Mapped[ContentSubmission] = relationship(back_populates="reviews")
    version: Mapped[ContentVersion] = relationship()
    analysis_run: Mapped[AnalysisRun | None] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id", "created_at"),)

    id: Mapped[uuid.UUID] = _pk()
    submission_id: Mapped[uuid.UUID | None] = _fk("content_submissions.id", nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = _created_at()
