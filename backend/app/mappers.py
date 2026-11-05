"""ORM to schema mappers shared by the API layer and the analysis pipeline.

Centrally controlled. Brand knowledge is exposed by stable code, never UUID.
"""

from app.models import BrandProfile
from app.schemas import BrandDetail, BrandKnowledge, Fact, Guideline, Term


def _guidelines(brand: BrandProfile) -> list[Guideline]:
    return [
        Guideline(id=g.code, title=g.title, text=g.rule_text, category=g.category, default_severity=g.default_severity)
        for g in brand.guidelines
        if g.is_active
    ]


def _facts(brand: BrandProfile) -> list[Fact]:
    return [Fact(id=f.code, statement=f.statement, source=f.source) for f in brand.facts if f.is_active]


def _terms(brand: BrandProfile) -> list[Term]:
    return [
        Term(
            id=t.code,
            preferred_term=t.preferred_term,
            prohibited_term=t.prohibited_term,
            notes=t.notes,
            related_guideline_id=t.related_guideline.code if t.related_guideline else None,
        )
        for t in brand.terms
        if t.is_active
    ]


def brand_to_knowledge(brand: BrandProfile) -> BrandKnowledge:
    return BrandKnowledge(brand_name=brand.name, guidelines=_guidelines(brand), facts=_facts(brand), terms=_terms(brand))


def brand_to_detail(brand: BrandProfile) -> BrandDetail:
    return BrandDetail(
        id=brand.id,
        slug=brand.slug,
        name=brand.name,
        industry=brand.industry,
        description=brand.description,
        is_demo=brand.is_demo,
        voice_summary=brand.voice_summary,
        guidelines=_guidelines(brand),
        facts=_facts(brand),
        terms=_terms(brand),
    )
