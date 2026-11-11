"""Analysis run retrieval router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.db import get_db
from app.models import User
from app.schemas import AnalysisRun
from app.services.submission_service import get_analysis_run

router = APIRouter(prefix="/api/analysis-runs", tags=["Analysis"])


@router.get("/{id}", response_model=AnalysisRun)
def get_run(
    id: UUID,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> AnalysisRun:
    return get_analysis_run(db, id, current_user=current_user)
