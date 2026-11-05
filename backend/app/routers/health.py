"""Health router providing public health probes."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.enums import AIStatus
from app.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    settings = get_settings()
    ai_status = AIStatus.OK if settings.ai_enabled else AIStatus.DISABLED

    return HealthResponse(
        status="ok",
        database=db_status,
        ai=ai_status,
    )
