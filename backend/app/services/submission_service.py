"""Submission service: business logic, state transitions, and audit logging."""

import uuid
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.enums import (
    ContentType,
    FindingSource,
    OverallStatus,
    ReviewDecision,
    SubmissionAction,
    SubmissionStatus,
)
from app.mappers import brand_to_knowledge
from app.models import (
    AnalysisRun,
    AuditLog,
    BrandProfile,
    ComplianceIssue,
    ContentSubmission,
    ContentVersion,
    HumanReview,
)
from app.schemas import (
    AnalysisRun as AnalysisRunSchema,
    AnalysisRunSummary,
    AuditLogEntry,
    ContentVersion as ContentVersionSchema,
    Finding as FindingSchema,
    HumanReview as HumanReviewSchema,
    SeverityCounts,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListItem,
    VersionCreate,
)
from app.services.analyzer import analyze_content


def _calc_allowed_actions(status: SubmissionStatus) -> list[SubmissionAction]:
    if status == SubmissionStatus.DRAFT:
        return [SubmissionAction.EDIT, SubmissionAction.ANALYZE]
    elif status == SubmissionStatus.ANALYZED:
        return [SubmissionAction.EDIT, SubmissionAction.ANALYZE, SubmissionAction.REQUEST_REVIEW]
    elif status == SubmissionStatus.IN_REVIEW:
        return [SubmissionAction.REVIEW]
    elif status == SubmissionStatus.REVISIONS_REQUESTED:
        return [SubmissionAction.EDIT, SubmissionAction.ANALYZE]
    return []


def log_audit(
    db: Session,
    submission_id: UUID | None,
    entity_type: str,
    entity_id: UUID,
    action: str,
    actor_name: str,
    details: dict[str, Any] | None = None,
) -> None:
    entry = AuditLog(
        submission_id=submission_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_name=actor_name,
        details=details or {},
    )
    db.add(entry)


def _to_run_summary(run: AnalysisRun) -> AnalysisRunSummary:
    counts = SeverityCounts()
    for issue in run.issues:
        sev = issue.severity.value
        if hasattr(counts, sev):
            setattr(counts, sev, getattr(counts, sev) + 1)

    return AnalysisRunSummary(
        id=run.id,
        version_id=run.version_id,
        version_number=run.version.version_number,
        overall_status=run.overall_status,
        requires_human_review=run.requires_human_review,
        ai_status=run.ai_status,
        finding_count=len(run.issues),
        severity_counts=counts,
        created_at=run.created_at,
    )


def _to_run_schema(run: AnalysisRun) -> AnalysisRunSchema:
    summary = _to_run_summary(run)
    findings = [
        FindingSchema(
            id=issue.id,
            position=issue.position,
            source=issue.source,
            category=issue.category,
            severity=issue.severity,
            finding_type=issue.finding_type,
            original_text=issue.original_text,
            start_offset=issue.start_offset,
            end_offset=issue.end_offset,
            guideline_id=issue.guideline.code if issue.guideline else None,
            approved_fact_id=issue.approved_fact.code if issue.approved_fact else None,
            approved_term_id=issue.approved_term.code if issue.approved_term else None,
            evidence=issue.evidence,
            explanation=issue.explanation,
            suggestion=issue.suggestion,
            confidence=issue.confidence,
            reference_note=issue.reference_note,
        )
        for issue in run.issues
    ]

    return AnalysisRunSchema(
        id=run.id,
        submission_id=run.submission_id,
        version_id=run.version_id,
        version_number=run.version.version_number,
        overall_status=run.overall_status,
        requires_human_review=run.requires_human_review,
        ai_status=run.ai_status,
        finding_count=len(run.issues),
        severity_counts=summary.severity_counts,
        summary=run.summary,
        positive_observations=run.positive_observations or [],
        model_name=run.model_name,
        rule_engine_version=run.rule_engine_version,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
        findings=findings,
    )


def create_submission(db: Session, payload: SubmissionCreate) -> ContentSubmission:
    brand = db.get(BrandProfile, payload.brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand {payload.brand_id} not found."},
        )

    submission = ContentSubmission(
        brand_id=brand.id,
        title=payload.title,
        content_type=payload.content_type,
        status=SubmissionStatus.DRAFT,
        current_version_number=1,
        author_name=payload.author_name or "Demo Editor",
    )
    db.add(submission)
    db.flush()

    v1 = ContentVersion(
        submission_id=submission.id,
        version_number=1,
        body=payload.body,
        change_note="Initial version",
    )
    db.add(v1)
    db.flush()

    log_audit(
        db,
        submission_id=submission.id,
        entity_type="content_submission",
        entity_id=submission.id,
        action="submission_created",
        actor_name=submission.author_name,
        details={"title": submission.title, "content_type": submission.content_type.value},
    )

    db.commit()
    db.refresh(submission)
    return submission


def list_submissions(
    db: Session,
    brand_id: UUID | None = None,
    submission_status: SubmissionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SubmissionListItem]:
    stmt = (
        select(ContentSubmission)
        .options(
            selectinload(ContentSubmission.brand),
            selectinload(ContentSubmission.analysis_runs),
        )
        .order_by(desc(ContentSubmission.updated_at))
        .offset(offset)
        .limit(limit)
    )
    if brand_id:
        stmt = stmt.where(ContentSubmission.brand_id == brand_id)
    if submission_status:
        stmt = stmt.where(ContentSubmission.status == submission_status)

    submissions = db.scalars(stmt).all()

    items: list[SubmissionListItem] = []
    for sub in submissions:
        latest_status = None
        if sub.analysis_runs:
            latest_status = sub.analysis_runs[-1].overall_status

        items.append(
            SubmissionListItem(
                id=sub.id,
                brand_id=sub.brand_id,
                brand_name=sub.brand.name,
                title=sub.title,
                content_type=sub.content_type,
                status=sub.status,
                current_version_number=sub.current_version_number,
                latest_overall_status=latest_status,
                author_name=sub.author_name,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
            )
        )
    return items


def get_submission_detail(db: Session, submission_id: UUID) -> SubmissionDetail:
    stmt = (
        select(ContentSubmission)
        .where(ContentSubmission.id == submission_id)
        .options(
            selectinload(ContentSubmission.brand),
            selectinload(ContentSubmission.versions).selectinload(ContentVersion.analysis_runs),
            selectinload(ContentSubmission.analysis_runs)
            .selectinload(AnalysisRun.issues)
            .selectinload(ComplianceIssue.guideline),
            selectinload(ContentSubmission.analysis_runs)
            .selectinload(AnalysisRun.issues)
            .selectinload(ComplianceIssue.approved_fact),
            selectinload(ContentSubmission.analysis_runs)
            .selectinload(AnalysisRun.issues)
            .selectinload(ComplianceIssue.approved_term),
            selectinload(ContentSubmission.analysis_runs).selectinload(AnalysisRun.version),
            selectinload(ContentSubmission.reviews).selectinload(HumanReview.version),
        )
    )
    sub = db.scalar(stmt)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Submission {submission_id} not found."},
        )

    versions_out: list[ContentVersionSchema] = []
    for v in sub.versions:
        versions_out.append(
            ContentVersionSchema(
                id=v.id,
                version_number=v.version_number,
                body=v.body,
                change_note=v.change_note,
                created_at=v.created_at,
                analysis_run_ids=[r.id for r in v.analysis_runs],
            )
        )

    run_summaries = [_to_run_summary(r) for r in sub.analysis_runs]

    # Current version and latest run on that version
    current_ver = next((v for v in sub.versions if v.version_number == sub.current_version_number), None)
    latest_run_schema = None
    if current_ver and current_ver.analysis_runs:
        latest_run = current_ver.analysis_runs[-1]
        latest_run_schema = _to_run_schema(latest_run)

    reviews_out = [
        HumanReviewSchema(
            id=rev.id,
            version_id=rev.version_id,
            version_number=rev.version.version_number,
            analysis_run_id=rev.analysis_run_id,
            reviewer_name=rev.reviewer_name,
            decision=rev.decision,
            comments=rev.comments,
            created_at=rev.created_at,
        )
        for rev in sub.reviews
    ]

    latest_status = sub.analysis_runs[-1].overall_status if sub.analysis_runs else None

    return SubmissionDetail(
        id=sub.id,
        brand_id=sub.brand_id,
        brand_name=sub.brand.name,
        title=sub.title,
        content_type=sub.content_type,
        status=sub.status,
        current_version_number=sub.current_version_number,
        latest_overall_status=latest_status,
        author_name=sub.author_name,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        versions=versions_out,
        analysis_runs=run_summaries,
        latest_analysis=latest_run_schema,
        reviews=reviews_out,
        allowed_actions=_calc_allowed_actions(sub.status),
    )


def create_version(db: Session, submission_id: UUID, payload: VersionCreate) -> ContentSubmission:
    sub = db.get(ContentSubmission, submission_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Submission {submission_id} not found."},
        )

    if sub.status in (SubmissionStatus.IN_REVIEW, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "invalid_state", "message": f"Cannot add a new version while submission is {sub.status.value}."},
        )

    next_version_num = sub.current_version_number + 1
    new_v = ContentVersion(
        submission_id=sub.id,
        version_number=next_version_num,
        body=payload.body,
        change_note=payload.change_note,
    )
    db.add(new_v)
    sub.current_version_number = next_version_num
    sub.status = SubmissionStatus.DRAFT
    db.flush()

    log_audit(
        db,
        submission_id=sub.id,
        entity_type="content_version",
        entity_id=new_v.id,
        action="version_created",
        actor_name=sub.author_name,
        details={"version_number": next_version_num, "change_note": payload.change_note},
    )

    db.commit()
    db.refresh(sub)
    return sub


def analyze_submission(db: Session, submission_id: UUID) -> AnalysisRunSchema:
    stmt = (
        select(ContentSubmission)
        .where(ContentSubmission.id == submission_id)
        .options(
            selectinload(ContentSubmission.brand).selectinload(BrandProfile.guidelines),
            selectinload(ContentSubmission.brand).selectinload(BrandProfile.facts),
            selectinload(ContentSubmission.brand).selectinload(BrandProfile.terms),
            selectinload(ContentSubmission.versions),
        )
    )
    sub = db.scalar(stmt)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Submission {submission_id} not found."},
        )

    if sub.status in (SubmissionStatus.IN_REVIEW, SubmissionStatus.APPROVED, SubmissionStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "invalid_state", "message": f"Cannot re-analyze while submission is {sub.status.value}."},
        )

    current_ver = next((v for v in sub.versions if v.version_number == sub.current_version_number), None)
    if not current_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Current content version not found."},
        )

    knowledge = brand_to_knowledge(sub.brand)
    analysis_res = analyze_content(current_ver.body, knowledge)

    run = AnalysisRun(
        submission_id=sub.id,
        version_id=current_ver.id,
        overall_status=analysis_res.overall_status,
        summary=analysis_res.summary,
        positive_observations=analysis_res.positive_observations,
        requires_human_review=analysis_res.requires_human_review,
        ai_status=analysis_res.ai_status,
        model_name=analysis_res.model_name,
        rule_engine_version=analysis_res.rule_engine_version,
        knowledge_snapshot=analysis_res.knowledge_snapshot,
        duration_ms=analysis_res.duration_ms,
    )
    db.add(run)
    db.flush()

    # Pre-fetch brand entity maps to link foreign keys
    guidelines_by_code = {g.code: g.id for g in sub.brand.guidelines}
    facts_by_code = {f.code: f.id for f in sub.brand.facts}
    terms_by_code = {t.code: t.id for t in sub.brand.terms}

    for pos, draft in enumerate(analysis_res.findings):
        issue = ComplianceIssue(
            analysis_run_id=run.id,
            position=pos,
            source=draft.source,
            category=draft.category,
            severity=draft.severity,
            finding_type=draft.finding_type,
            original_text=draft.original_text,
            start_offset=draft.start_offset,
            end_offset=draft.end_offset,
            guideline_id=guidelines_by_code.get(draft.guideline_id) if draft.guideline_id else None,
            approved_fact_id=facts_by_code.get(draft.approved_fact_id) if draft.approved_fact_id else None,
            approved_term_id=terms_by_code.get(draft.approved_term_id) if draft.approved_term_id else None,
            evidence=draft.evidence,
            explanation=draft.explanation,
            suggestion=draft.suggestion,
            confidence=draft.confidence,
            reference_note=draft.reference_note,
        )
        db.add(issue)

    sub.status = SubmissionStatus.ANALYZED
    db.flush()

    log_audit(
        db,
        submission_id=sub.id,
        entity_type="analysis_run",
        entity_id=run.id,
        action="analysis_completed",
        actor_name="Inkloom Engine",
        details={
            "overall_status": run.overall_status.value,
            "finding_count": len(analysis_res.findings),
            "ai_status": run.ai_status.value,
        },
    )

    db.commit()

    # Reload with relations to construct full schema
    return get_analysis_run(db, run.id)


def get_analysis_run(db: Session, run_id: UUID) -> AnalysisRunSchema:
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.id == run_id)
        .options(
            selectinload(AnalysisRun.version),
            selectinload(AnalysisRun.issues).selectinload(ComplianceIssue.guideline),
            selectinload(AnalysisRun.issues).selectinload(ComplianceIssue.approved_fact),
            selectinload(AnalysisRun.issues).selectinload(ComplianceIssue.approved_term),
        )
    )
    run = db.scalar(stmt)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Analysis run {run_id} not found."},
        )
    return _to_run_schema(run)


def request_review(db: Session, submission_id: UUID, requested_by: str, note: str | None = None) -> ContentSubmission:
    sub = db.get(ContentSubmission, submission_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Submission {submission_id} not found."},
        )

    if sub.status != SubmissionStatus.ANALYZED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "invalid_state", "message": "Only analyzed content can be submitted for review."},
        )

    sub.status = SubmissionStatus.IN_REVIEW
    db.flush()

    log_audit(
        db,
        submission_id=sub.id,
        entity_type="content_submission",
        entity_id=sub.id,
        action="review_requested",
        actor_name=requested_by,
        details={"note": note},
    )

    db.commit()
    db.refresh(sub)
    return sub


def record_review(
    db: Session,
    submission_id: UUID,
    decision: ReviewDecision,
    reviewer_name: str,
    comments: str | None,
) -> ContentSubmission:
    stmt = (
        select(ContentSubmission)
        .where(ContentSubmission.id == submission_id)
        .options(
            selectinload(ContentSubmission.versions).selectinload(ContentVersion.analysis_runs),
        )
    )
    sub = db.scalar(stmt)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Submission {submission_id} not found."},
        )

    if sub.status != SubmissionStatus.IN_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "invalid_state", "message": f"Cannot review content with status {sub.status.value}."},
        )

    current_ver = next((v for v in sub.versions if v.version_number == sub.current_version_number), None)
    if not current_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Current version not found."},
        )

    latest_run = current_ver.analysis_runs[-1] if current_ver.analysis_runs else None

    # Status mapping from decision
    if decision == ReviewDecision.APPROVED:
        sub.status = SubmissionStatus.APPROVED
    elif decision == ReviewDecision.REJECTED:
        sub.status = SubmissionStatus.REJECTED
    elif decision == ReviewDecision.REVISIONS_REQUESTED:
        sub.status = SubmissionStatus.REVISIONS_REQUESTED

    review = HumanReview(
        submission_id=sub.id,
        version_id=current_ver.id,
        analysis_run_id=latest_run.id if latest_run else None,
        reviewer_name=reviewer_name,
        decision=decision,
        comments=comments,
    )
    db.add(review)
    db.flush()

    log_audit(
        db,
        submission_id=sub.id,
        entity_type="human_review",
        entity_id=review.id,
        action="review_recorded",
        actor_name=reviewer_name,
        details={"decision": decision.value, "comments": comments},
    )

    db.commit()
    db.refresh(sub)
    return sub


def get_audit_trail(db: Session, submission_id: UUID) -> list[AuditLogEntry]:
    stmt = (
        select(AuditLog)
        .where(AuditLog.submission_id == submission_id)
        .order_by(AuditLog.created_at)
    )
    entries = db.scalars(stmt).all()
    return [
        AuditLogEntry(
            id=e.id,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            action=e.action,
            actor_name=e.actor_name,
            details=e.details or {},
            created_at=e.created_at,
        )
        for e in entries
    ]
