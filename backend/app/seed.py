"""Idempotent seed for the fictional LumaCare demo brand.

Centrally controlled contract file. Brand knowledge text below is the exact
approved wording from the project brief. Do not add product efficacy claims.

Run manually:  python -m app.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import FindingCategory, Severity, UserRole
from app.models import ApprovedFact, ApprovedTerm, BrandGuideline, BrandProfile, Organisation, User

DEMO_ORG_SLUG = "lumacare-demo"
DEMO_BRAND_SLUG = "lumacare"

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

USERS = [
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

    for u in USERS:
        if db.scalar(select(User).where(User.email == u["email"])) is None:
            db.add(User(organisation_id=org.id, **u))

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

    db.commit()
    return brand


if __name__ == "__main__":
    from app.db import SessionLocal, init_db

    init_db()
    with SessionLocal() as session:
        seeded = seed_demo_data(session)
        print(f"Seeded brand {seeded.name} ({seeded.id})")
