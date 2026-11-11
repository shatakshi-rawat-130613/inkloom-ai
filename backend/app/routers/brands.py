"""Brand workspace router with multi-tenant isolation and brand governance."""

import re
import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_current_user, get_optional_user, require_admin
from app.db import get_db
from app.mappers import brand_to_detail
from app.models import ApprovedFact, ApprovedTerm, BrandAsset, BrandGuideline, BrandProfile, User
from app.schemas import (
    BrandAssetCreateRequest,
    BrandAssetResponse,
    BrandCreateRequest,
    BrandDetail,
    BrandSummary,
    BrandUpdateRequest,
    FactCreateRequest,
    GuidelineCreateRequest,
    TermCreateRequest,
)

router = APIRouter(prefix="/api/brands", tags=["Brands"])


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return cleaned[:50] or "brand"


def _verify_brand_access(brand: BrandProfile, user: User | None) -> None:
    if brand.is_demo:
        return
    if user is None or brand.organisation_id != user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand not found or access denied."},
        )


def _asset_to_response(asset: BrandAsset) -> BrandAssetResponse:
    return BrandAssetResponse(
        id=asset.id,
        brand_id=asset.brand_id,
        asset_type=asset.asset_type,
        name=asset.name,
        asset_metadata=asset.asset_metadata,
        is_active=asset.is_active,
        created_at=asset.created_at,
    )


@router.get("", response_model=list[BrandSummary])
def list_brands(
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> list[BrandSummary]:
    """List brands accessible to the caller: public demo brand plus caller's organisation brands."""
    if current_user is not None:
        stmt = (
            select(BrandProfile)
            .where(
                or_(
                    BrandProfile.is_demo.is_(True),
                    BrandProfile.organisation_id == current_user.organisation_id,
                )
            )
            .order_by(BrandProfile.name)
        )
    else:
        stmt = select(BrandProfile).where(BrandProfile.is_demo.is_(True)).order_by(BrandProfile.name)

    brands = db.scalars(stmt).all()
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


@router.post("", response_model=BrandDetail, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: BrandCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Create a new brand workspace within the caller's organisation. Requires Brand Manager (ADMIN)."""
    base_slug = _slugify(payload.name)
    slug = base_slug
    suffix = 1
    while db.scalar(select(BrandProfile).where(BrandProfile.slug == slug)) is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    brand = BrandProfile(
        organisation_id=current_user.organisation_id,
        slug=slug,
        name=payload.name.strip(),
        industry=payload.industry.strip(),
        description=payload.description.strip(),
        voice_summary=payload.voice_summary.strip(),
        is_demo=False,
    )
    db.add(brand)
    db.commit()

    # Re-fetch with relationships loaded
    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand.id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    brand = db.scalar(stmt)
    return brand_to_detail(brand)


@router.get("/{identifier}", response_model=BrandDetail)
def get_brand(
    identifier: str,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Get brand workspace details by slug or UUID with tenant isolation."""
    stmt = select(BrandProfile).options(
        selectinload(BrandProfile.guidelines),
        selectinload(BrandProfile.facts),
        selectinload(BrandProfile.terms),
        selectinload(BrandProfile.assets),
    )
    try:
        brand_id = UUID(identifier)
        stmt = stmt.where(BrandProfile.id == brand_id)
    except ValueError:
        stmt = stmt.where(BrandProfile.slug == identifier)

    brand = db.scalar(stmt)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{identifier}' not found."},
        )

    _verify_brand_access(brand, current_user)
    return brand_to_detail(brand)


@router.patch("/{brand_id}", response_model=BrandDetail)
def update_brand(
    brand_id: UUID,
    payload: BrandUpdateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Update brand profile attributes. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )

    if payload.name is not None:
        brand.name = payload.name.strip()
    if payload.industry is not None:
        brand.industry = payload.industry.strip()
    if payload.description is not None:
        brand.description = payload.description.strip()
    if payload.voice_summary is not None:
        brand.voice_summary = payload.voice_summary.strip()

    db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    brand = db.scalar(stmt)
    return brand_to_detail(brand)


@router.post("/{brand_id}/guidelines", response_model=BrandDetail, status_code=status.HTTP_201_CREATED)
def add_guideline(
    brand_id: UUID,
    payload: GuidelineCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Add a compliance guideline to a brand workspace. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )

    guideline = BrandGuideline(
        brand_id=brand.id,
        code=payload.code.strip().upper(),
        title=payload.title.strip(),
        rule_text=payload.rule_text.strip(),
        category=payload.category,
        default_severity=payload.default_severity,
        is_active=True,
    )
    db.add(guideline)
    db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.post("/{brand_id}/facts", response_model=BrandDetail, status_code=status.HTTP_201_CREATED)
def add_fact(
    brand_id: UUID,
    payload: FactCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Add an approved factual statement to a brand workspace. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )

    fact = ApprovedFact(
        brand_id=brand.id,
        code=payload.code.strip().upper(),
        statement=payload.statement.strip(),
        source=payload.source.strip() if payload.source else None,
        is_active=True,
    )
    db.add(fact)
    db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.post("/{brand_id}/terms", response_model=BrandDetail, status_code=status.HTTP_201_CREATED)
def add_term(
    brand_id: UUID,
    payload: TermCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Add approved terminology rules to a brand workspace. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )

    related_id = None
    if payload.related_guideline_code:
        rel = db.scalar(
            select(BrandGuideline).where(
                BrandGuideline.brand_id == brand.id,
                BrandGuideline.code == payload.related_guideline_code.strip().upper(),
            )
        )
        if rel:
            related_id = rel.id

    term = ApprovedTerm(
        brand_id=brand.id,
        code=payload.code.strip().upper(),
        preferred_term=payload.preferred_term.strip() if payload.preferred_term else None,
        prohibited_term=payload.prohibited_term.strip() if payload.prohibited_term else None,
        notes=payload.notes.strip() if payload.notes else None,
        related_guideline_id=related_id,
        is_active=True,
    )
    db.add(term)
    db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.get("/{brand_id}/assets", response_model=list[BrandAssetResponse])
def list_brand_assets(
    brand_id: UUID,
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
    db: Session = Depends(get_db),
) -> list[BrandAssetResponse]:
    """List visual assets configured for a brand workspace."""
    brand = db.get(BrandProfile, brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )
    _verify_brand_access(brand, current_user)

    assets = db.scalars(
        select(BrandAsset)
        .where(BrandAsset.brand_id == brand_id, BrandAsset.is_active.is_(True))
        .order_by(BrandAsset.created_at)
    ).all()
    return [_asset_to_response(a) for a in assets]


@router.post("/{brand_id}/assets", response_model=BrandAssetResponse, status_code=status.HTTP_201_CREATED)
def create_brand_asset(
    brand_id: UUID,
    payload: BrandAssetCreateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandAssetResponse:
    """Add a visual brand asset (logo, color palette, visual guideline). Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )

    asset = BrandAsset(
        brand_id=brand.id,
        asset_type=payload.asset_type.strip(),
        name=payload.name.strip(),
        asset_metadata=payload.asset_metadata,
        is_active=True,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _asset_to_response(asset)


@router.delete("/{brand_id}/guidelines/{code}", response_model=BrandDetail)
def delete_guideline(
    brand_id: UUID,
    code: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Deactivate a guideline rule. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )
    g = db.scalar(
        select(BrandGuideline).where(
            BrandGuideline.brand_id == brand.id,
            BrandGuideline.code == code.strip().upper(),
        )
    )
    if g:
        g.is_active = False
        db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.delete("/{brand_id}/facts/{code}", response_model=BrandDetail)
def delete_fact(
    brand_id: UUID,
    code: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Deactivate an approved factual statement. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )
    f = db.scalar(
        select(ApprovedFact).where(
            ApprovedFact.brand_id == brand.id,
            ApprovedFact.code == code.strip().upper(),
        )
    )
    if f:
        f.is_active = False
        db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.delete("/{brand_id}/terms/{code}", response_model=BrandDetail)
def delete_term(
    brand_id: UUID,
    code: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> BrandDetail:
    """Deactivate an approved term rule. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )
    t = db.scalar(
        select(ApprovedTerm).where(
            ApprovedTerm.brand_id == brand.id,
            ApprovedTerm.code == code.strip().upper(),
        )
    )
    if t:
        t.is_active = False
        db.commit()

    stmt = (
        select(BrandProfile)
        .where(BrandProfile.id == brand_id)
        .options(
            selectinload(BrandProfile.guidelines),
            selectinload(BrandProfile.facts),
            selectinload(BrandProfile.terms),
            selectinload(BrandProfile.assets),
        )
    )
    return brand_to_detail(db.scalar(stmt))


@router.delete("/{brand_id}/assets/{asset_id}", response_model=list[BrandAssetResponse])
def delete_brand_asset(
    brand_id: UUID,
    asset_id: UUID,
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
) -> list[BrandAssetResponse]:
    """Deactivate a visual brand asset. Requires Brand Manager (ADMIN)."""
    brand = db.get(BrandProfile, brand_id)
    if not brand or brand.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": f"Brand '{brand_id}' not found."},
        )
    asset = db.get(BrandAsset, asset_id)
    if asset and asset.brand_id == brand.id:
        asset.is_active = False
        db.commit()

    assets = db.scalars(
        select(BrandAsset)
        .where(BrandAsset.brand_id == brand_id, BrandAsset.is_active.is_(True))
        .order_by(BrandAsset.created_at)
    ).all()
    return [_asset_to_response(a) for a in assets]
