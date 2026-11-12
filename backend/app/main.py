"""Inkloom AI FastAPI application.

Provides brand governance APIs, deterministic and Gemini-based compliance analysis,
versioned content workflows, and human review decisions.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.routers import analysis, auth, brands, documents, health, submissions
from app.schemas import ErrorBody, ErrorResponse
from app.seed import seed_demo_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inkloom")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and demo brand is seeded if configured
    logger.info("Initializing database tables and seed data...")
    init_db()
    with SessionLocal() as session:
        try:
            seed_demo_data(session)
        except ValueError as exc:
            logger.info("Demo account seeding skipped on startup: %s", exc)
    logger.info("Startup complete.")
    yield


settings = get_settings()

app = FastAPI(
    title="Inkloom AI API",
    description="Intelligent Brand-Governance Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
origins = settings.cors_origin_list
if not origins:
    origins = ["http://localhost:5173", "https://inkloom-ai-wheat.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers adhering to ErrorResponse schema
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        body = ErrorBody(
            code=exc.detail["code"],
            message=exc.detail.get("message", "An error occurred"),
            details=exc.detail.get("details"),
        )
    else:
        body = ErrorBody(
            code="error",
            message=str(exc.detail),
            details=None,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=body).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        loc = " -> ".join(str(item) for item in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        details.append({"loc": loc, "msg": msg})

    body = ErrorBody(
        code="validation_error",
        message="Request validation failed.",
        details=details,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(error=body).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    body = ErrorBody(
        code="internal_error",
        message="An unexpected server error occurred. Please try again later.",
        details=None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(error=body).model_dump(mode="json"),
    )


# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(submissions.router)
app.include_router(analysis.router)
app.include_router(documents.router)
