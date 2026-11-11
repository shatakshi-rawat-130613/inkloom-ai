"""Document, PDF and visual asset upload and extraction router."""

import os
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_optional_user
from app.db import get_db
from app.models import BrandProfile, DocumentExtraction, User
from app.schemas import DocumentExtractResponse, FindingDraft
from app.services.document_service import (
    analyze_image_visual_compliance,
    extract_pdf_content,
    extract_text_content,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/extract", response_model=DocumentExtractResponse)
async def extract_document(
    file: Annotated[UploadFile, File(...)],
    brand_id: Annotated[UUID | None, Form()] = None,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> DocumentExtractResponse:
    """Extract text, document structure, and visual brand compliance from uploaded files."""
    filename = file.filename or "uploaded_file"
    _, ext = os.path.splitext(filename.lower())

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum permitted limit (10MB).",
        )

    # Load brand assets if brand_id provided
    brand_assets = []
    if brand_id:
        brand = db.scalar(
            select(BrandProfile)
            .where(BrandProfile.id == brand_id)
            .options(selectinload(BrandProfile.assets))
        )
        if brand:
            brand_assets = brand.assets

    visual_findings: list[FindingDraft] = []

    if ext == ".pdf":
        try:
            extracted_text, metadata = extract_pdf_content(file_bytes, filename)
            source = "document"
            ftype = "pdf"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse PDF document: {str(e)}",
            )
    elif ext in {".txt", ".md"}:
        try:
            extracted_text, metadata = extract_text_content(file_bytes, filename)
            source = "document"
            ftype = "text"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to read text document: {str(e)}",
            )
    else:  # Image formats
        try:
            extracted_text, metadata, visual_findings = analyze_image_visual_compliance(
                file_bytes, filename, brand_assets=brand_assets
            )
            source = "visual"
            ftype = f"image/{ext.lstrip('.')}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to process visual image asset: {str(e)}",
            )

    # Persist extraction record
    extraction = DocumentExtraction(
        file_name=filename,
        file_type=ftype,
        file_size_bytes=file_size,
        extraction_source=source,
        extracted_text=extracted_text,
        extraction_status="completed",
        extraction_metadata=metadata,
    )
    db.add(extraction)
    db.commit()

    return DocumentExtractResponse(
        file_name=filename,
        file_type=ftype,
        file_size_bytes=file_size,
        extraction_source=source,
        extracted_text=extracted_text,
        extraction_metadata=metadata,
        visual_findings=visual_findings,
    )
