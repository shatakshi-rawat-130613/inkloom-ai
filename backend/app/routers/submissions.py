"""Content submissions, versions, analysis triggers, and human review router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.db import get_db
from app.enums import SubmissionStatus
from app.models import User
from app.schemas import (
    AnalysisRun,
    AuditLogEntry,
    ReviewCreate,
    ReviewRequestCreate,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionListItem,
    VersionCreate,
)
from app.services.submission_service import (
    analyze_submission,
    create_submission,
    create_version,
    get_audit_trail,
    get_submission_detail,
    list_submissions,
    record_review,
    request_review,
)

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])


@router.post("", response_model=SubmissionDetail, status_code=status.HTTP_201_CREATED)
def submit_content(
    payload: SubmissionCreate,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    sub = create_submission(db, payload, current_user=current_user)
    return get_submission_detail(db, sub.id, current_user=current_user)


@router.get("", response_model=list[SubmissionListItem])
def get_submissions(
    brand_id: UUID | None = None,
    status: SubmissionStatus | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> list[SubmissionListItem]:
    return list_submissions(
        db,
        brand_id=brand_id,
        submission_status=status,
        limit=limit,
        offset=offset,
        current_user=current_user,
    )


@router.get("/{id}", response_model=SubmissionDetail)
def get_submission(
    id: UUID,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    return get_submission_detail(db, id, current_user=current_user)


@router.post("/{id}/versions", response_model=SubmissionDetail, status_code=status.HTTP_201_CREATED)
def add_version(
    id: UUID,
    payload: VersionCreate,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    sub = create_version(db, id, payload, current_user=current_user)
    return get_submission_detail(db, sub.id, current_user=current_user)


@router.post("/{id}/analyze", response_model=AnalysisRun, status_code=status.HTTP_201_CREATED)
def run_analysis(
    id: UUID,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> AnalysisRun:
    return analyze_submission(db, id, current_user=current_user)


@router.post("/{id}/review-request", response_model=SubmissionDetail)
def submit_for_review(
    id: UUID,
    payload: ReviewRequestCreate = ReviewRequestCreate(),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    sub = request_review(
        db,
        id,
        requested_by=payload.requested_by,
        note=payload.note,
        current_user=current_user,
    )
    return get_submission_detail(db, sub.id, current_user=current_user)


@router.post("/{id}/reviews", response_model=SubmissionDetail, status_code=status.HTTP_201_CREATED)
def submit_review(
    id: UUID,
    payload: ReviewCreate,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> SubmissionDetail:
    sub = record_review(
        db,
        submission_id=id,
        decision=payload.decision,
        reviewer_name=payload.reviewer_name,
        comments=payload.comments,
        current_user=current_user,
    )
    return get_submission_detail(db, sub.id, current_user=current_user)


@router.get("/{id}/audit", response_model=list[AuditLogEntry])
def get_audit(
    id: UUID,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> list[AuditLogEntry]:
    return get_audit_trail(db, id, current_user=current_user)
