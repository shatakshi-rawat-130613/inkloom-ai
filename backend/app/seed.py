"""Idempotent seed for the fictional LumaCare demo brand.

Centrally controlled contract file. Brand knowledge text below is the exact
approved wording from the project brief. Do not add product efficacy claims.

Run manually:  python -m app.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.enums import FindingCategory, Severity, UserRole
from app.models import ApprovedFact, ApprovedTerm, BrandAsset, BrandGuideline, BrandProfile, Organisation, User

DEMO_ORG_SLUG = "lumacare-demo"
DEMO_BRAND_SLUG = "lumacare"
DEMO_PASSWORD = "LumaCareDemo2026!"

ORGANISATION = {"slug": DEMO_ORG_SLUG, "name": "LumaCare (fictional demo organisation)"}

BRAND = {
    "slug": DEMO_BRAND_SLUG,
    "name": "LumaCare",
    "industry": "Skincare",
    "description": (
        "LumaCare is a fictional skincare brand created to demonstrate Inkloom AI. "
        "Its demo product is a facial cream. All brand knowledge shown here is illustrative."
    ),
    "voice_summary": "Friendly, reassuring and realistic. Claims stay within approved product information.",
    "is_demo": True,
}

GUIDELINES = [
    {
        "code": "GUIDE-001",
        "title": "No guaranteed outcomes",
        "rule_text": "Do not promise guaranteed medical or skincare outcomes.",
        "category": FindingCategory.OUTCOME_CLAIM,
        "default_severity": Severity.HIGH,
    },
    {
        "code": "GUIDE-002",
        "title": "Friendly and realistic tone",
        "rule_text": "Use friendly, reassuring and realistic messaging.",
        "category": FindingCategory.TONE,
        "default_severity": Severity.MEDIUM,
    },
    {
        "code": "GUIDE-003",
        "title": "Consistency with approved information",
        "rule_text": "Claims must be consistent with approved product information.",
        "category": FindingCategory.FACTUAL_CONSISTENCY,
        "default_severity": Severity.HIGH,
    },
]

FACTS = [
    {"code": "FACT-001", "statement": "The product is designed to support clearer-looking skin.", "source": "LumaCare approved product information (demo)"},
    {"code": "FACT-002", "statement": "No guaranteed acne-removal timeframe has been approved.", "source": "LumaCare approved product information (demo)"},
]

TERMS = [
    {
        "code": "TERM-001",
        "preferred_term": "supports clearer-looking skin",
        "prohibited_term": "guaranteed acne removal",
        "notes": "Use the preferred wording when describing product benefits.",
        "related_guideline_code": "GUIDE-001",
    },
]

ASSETS = [
    {
        "asset_type": "logo",
        "name": "LumaCare Primary Wordmark",
        "asset_metadata": {
            "text": "LumaCare",
            "aspect_ratio": "3:1",
            "min_width_px": 120,
            "min_clearance_px": 24,
            "acceptable_variants": ["LumaCare", "LUMACARE", "lumacare"],
            "primary_color": "#1C1917",
        },
    },
    {
        "asset_type": "color_palette",
        "name": "LumaCare Approved Color Palette",
        "asset_metadata": {
            "colors": [
                {"name": "Ivory", "hex": "#FDFBF7", "role": "primary_background"},
                {"name": "Parchment", "hex": "#F4EFE6", "role": "secondary_background"},
                {"name": "Ink", "hex": "#1C1917", "role": "primary_text"},
                {"name": "Sage", "hex": "#3B5E4F", "role": "accent_compliant"},
                {"name": "Terracotta", "hex": "#9C4132", "role": "accent_warning"},
            ],
            "max_color_delta_e": 25.0,
        },
    },
    {
        "asset_type": "visual_guideline",
        "name": "LumaCare Imagery & Composition Standards",
        "asset_metadata": {
            "min_contrast_ratio": 4.5,
            "imagery_style": "Natural, realistic skincare lighting, no heavy artificial filters or distorted proportions.",
            "unapproved_visual_elements": ["medical syringe imagery", "dramatic fake before-after splits"],
        },
    },
]

USERS = [
    {"display_name": "Demo Brand Manager", "email": "admin@lumacare.demo", "role": UserRole.ADMIN},
    {"display_name": "Demo Editor", "email": "editor@lumacare.demo", "role": UserRole.EDITOR},
    {"display_name": "Demo Reviewer", "email": "reviewer@lumacare.demo", "role": UserRole.REVIEWER},
]


def seed_demo_data(db: Session) -> BrandProfile:
    """Insert missing demo records. Safe to call on every startup."""
    org = db.scalar(select(Organisation).where(Organisation.slug == DEMO_ORG_SLUG))
    if org is None:
        org = Organisation(**ORGANISATION)
        db.add(org)
        db.flush()

    default_pwd_hash = hash_password(DEMO_PASSWORD)

    for u in USERS:
        existing_user = db.scalar(select(User).where(User.email == u["email"]))
        if existing_user is None:
            db.add(User(organisation_id=org.id, password_hash=default_pwd_hash, **u))
        elif existing_user.password_hash is None:
            existing_user.password_hash = default_pwd_hash

    brand = db.scalar(select(BrandProfile).where(BrandProfile.slug == DEMO_BRAND_SLUG))
    if brand is None:
        brand = BrandProfile(organisation_id=org.id, **BRAND)
        db.add(brand)
        db.flush()

    existing_guidelines = {g.code: g for g in db.scalars(select(BrandGuideline).where(BrandGuideline.brand_id == brand.id))}
    for g in GUIDELINES:
        if g["code"] not in existing_guidelines:
            row = BrandGuideline(brand_id=brand.id, **g)
            db.add(row)
            existing_guidelines[g["code"]] = row
    db.flush()

    existing_facts = {f.code for f in db.scalars(select(ApprovedFact).where(ApprovedFact.brand_id == brand.id))}
    for f in FACTS:
        if f["code"] not in existing_facts:
            db.add(ApprovedFact(brand_id=brand.id, **f))

    existing_terms = {t.code for t in db.scalars(select(ApprovedTerm).where(ApprovedTerm.brand_id == brand.id))}
    for t in TERMS:
        if t["code"] not in existing_terms:
            data = dict(t)
            related = existing_guidelines.get(data.pop("related_guideline_code"))
            db.add(ApprovedTerm(brand_id=brand.id, related_guideline_id=related.id if related else None, **data))

    existing_assets = {a.name for a in db.scalars(select(BrandAsset).where(BrandAsset.brand_id == brand.id))}
    for a in ASSETS:
        if a["name"] not in existing_assets:
            db.add(BrandAsset(brand_id=brand.id, **a))

    db.commit()
    return brand

    db.commit()
    return brand


if __name__ == "__main__":
    from app.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as session:
        seeded = seed_demo_data(session)
        print(f"Seeded brand {seeded.name} ({seeded.id})")
