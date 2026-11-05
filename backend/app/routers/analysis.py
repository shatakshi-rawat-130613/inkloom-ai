"""Analysis run retrieval router."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AnalysisRun
from app.services.submission_service import get_analysis_run

router = APIRouter(prefix="/api/analysis-runs", tags=["Analysis"])


@router.get("/{id}", response_model=AnalysisRun)
def get_run(id: UUID, db: Session = Depends(get_db)) -> AnalysisRun:
    return get_analysis_run(db, id)
