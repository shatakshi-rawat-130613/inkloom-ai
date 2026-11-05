import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, Query
from google import genai
from google.genai import types
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.enums import AIStatus
from app.schemas import AIAnalysisOutput, HealthResponse
from app.services.gemini_service import sanitize_error

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


@router.get("/api/debug/ai")
def debug_ai(
    model: str | None = Query(default=None, description="Optional model to test"),
    test_case: int = Query(default=2, ge=1, le=3, description="LumaCare test case: 1=non-compliant, 2=compliant, 3=partially-compliant"),
    skip_test: bool = Query(default=False, description="Skip generation test"),
) -> dict[str, Any]:
    """Diagnostic probe to verify Gemini API model availability and structured JSON output."""
    settings = get_settings()

    if not settings.gemini_api_key:
        return {
            "api_key_configured": False,
            "status": "disabled",
            "message": "GEMINI_API_KEY is not set in environment.",
        }

    target_model = model or settings.gemini_model
    target_clean = target_model.strip()

    available_models: list[str] = []
    list_error: str | None = None

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        for m in client.models.list():
            if m.name:
                available_models.append(m.name.replace("models/", ""))
    except Exception as exc:
        list_error = f"{type(exc).__name__}: {sanitize_error(exc)}"

    test_result: dict[str, Any] = {
        "model_tested": target_clean,
        "test_case_number": test_case,
        "success": False,
        "exception_type": None,
        "exception_message": None,
        "output_summary": None,
        "findings_count": 0,
        "findings": [],
        "positive_observations": [],
    }

    if not skip_test:
        test_inputs = {
            1: "Our revolutionary cream guarantees 100% acne removal in just 2 days! Buy now and get flawless skin instantly.",
            2: "Discover a simple addition to your skincare routine with LumaCare. Our cream is designed to support clearer-looking skin. Enjoy a gentle, reassuring approach to everyday skincare.",
            3: "Make your skincare routine simpler with LumaCare. Our cream supports clearer-looking skin and helps reduce acne within 7 days. Experience a gentle approach to everyday skincare.",
        }
        chosen_content = test_inputs[test_case]

        try:
            client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=30000),
            )
            config = types.GenerateContentConfig(
                system_instruction="You are Inkloom AI. Evaluate content against brand standards.",
                response_mime_type="application/json",
                response_schema=AIAnalysisOutput,
                temperature=0.0,
            )

            test_prompt = f"""BRAND: LumaCare
APPROVED GUIDELINES:
- [GUIDE-001] No guaranteed outcomes (outcome_claim, severity: high): Do not promise guaranteed medical or skincare outcomes.
- [GUIDE-002] Friendly and realistic tone (tone, severity: medium): Use friendly, reassuring and realistic messaging.
- [GUIDE-003] Consistency with approved information (factual_consistency, severity: high): Claims must be consistent with approved product information.

APPROVED FACTS:
- [FACT-001]: The product is designed to support clearer-looking skin.
- [FACT-002]: No guaranteed acne-removal timeframe has been approved.

APPROVED / PROHIBITED TERMINOLOGY:
- [TERM-001] Preferred: 'supports clearer-looking skin' | Prohibited: 'guaranteed acne removal'

SUBMITTED CONTENT TO ANALYSE:
"{chosen_content}"
"""

            response = client.models.generate_content(
                model=target_clean,
                contents=test_prompt,
                config=config,
            )

            if response.text:
                parsed = AIAnalysisOutput.model_validate_json(response.text)
                test_result["success"] = True
                test_result["output_summary"] = parsed.summary
                test_result["findings_count"] = len(parsed.findings)
                test_result["findings"] = [f.model_dump() for f in parsed.findings]
                test_result["positive_observations"] = parsed.positive_observations
            else:
                test_result["exception_message"] = "Empty text in response"

        except Exception as exc:
            test_result["exception_type"] = type(exc).__name__
            test_result["exception_message"] = sanitize_error(exc)

    return {
        "api_key_configured": True,
        "configured_default_model": settings.gemini_model,
        "target_model": target_clean,
        "list_models_error": list_error,
        "available_models_count": len(available_models),
        "available_models": available_models,
        "test_call": test_result if not skip_test else "skipped",
    }
