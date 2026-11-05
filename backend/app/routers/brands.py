"""Brand workspace router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.mappers import brand_to_detail
from app.models import BrandProfile
from app.schemas import BrandDetail, BrandSummary

router = APIRouter(prefix="/api/brands", tags=["Brands"])


@router.get("", response_model=list[BrandSummary])
def list_brands(db: Session = Depends(get_db)) -> list[BrandSummary]:
    brands = db.scalars(select(BrandProfile).order_by(BrandProfile.name)).all()
    return [
        BrandSummary(
            id=b.id,
            slug=b.slug,
            name=b.name,
            industry=b.industry,
            description=b.description,
            is_demo=b.is_demo,
        )
        for b in brands
    ]


@router.get("/{slug}", response_model=BrandDetail)
def get_brand_by_slug(slug: str, db: Session = Depends(get_db)) -> BrandDetail:
    stmt = (
        select(BrandProfile)
        .where(BrandProfile.slug == slug)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
        )
    )
    brand = db.scalar(stmt)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{slug}' not found."},
        )
    return brand_to_detail(brand)
