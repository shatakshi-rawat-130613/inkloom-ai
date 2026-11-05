"""Brand relevance assessment service for Inkloom AI.

Evaluates whether submitted content relates to the active brand prior to
applying brand-specific compliance rules and guidelines.

Categorisation:
1. RELEVANT: Relates to the active brand (brand name, products, domain, terminology).
2. INSUFFICIENT_CONTEXT: Very short messages, generic pleasantries, or copy lacking context.
3. UNRELATED: Content clearly describes another brand, industry, or product category.
"""

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Sequence

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import BrandKnowledge, FindingDraft

SKINCARE_KEYWORDS = {
    "skin", "skincare", "complexion", "cream", "creams", "moisturizer", "moisturizers",
    "cleanser", "cleansers", "serum", "serums", "lotion", "lotions", "dermatologist",
    "dermatology", "dermatologist-tested", "dermatological", "acne", "blemish",
    "blemishes", "pore", "pores", "breakout", "breakouts", "exfoliate", "exfoliating",
    "exfoliation", "hydrating", "hydration", "skin-barrier", "barrier", "niacinamide",
    "zinc", "pca", "comedogenic", "non-comedogenic", "facial", "facials", "wrinkle",
    "wrinkles", "retinol", "sunscreen", "spf", "patch testing", "soothing", "clarifying",
    "topical", "epidermis"
}

UNRELATED_FOOD_KEYWORDS = {
    "food", "foods", "beverage", "beverages", "snack", "snacks", "meal", "meals",
    "granola", "chickpeas", "chickpea", "breakfast", "dinner", "lunch", "pantry",
    "cooking", "cook", "recipe", "recipes", "flavour", "flavours", "flavor", "flavors",
    "taste", "tasty", "delicious", "eating", "eat", "eats", "ingredient", "ingredients",
    "diet", "dietary", "nutrition", "nutritional", "calories", "grain", "grains",
    "oats", "seed", "seeds", "nuts", "crackers", "lentil", "lentils", "kitchen",
    "baking", "ready-to-cook", "meal kit", "meal kits", "dish", "dishes", "packaged food",
    "edible", "grocery", "groceries", "dining", "culinary", "dairy", "spices", "spreads"
}

UNRELATED_AUTOMOTIVE_KEYWORDS = {
    "automotive", "vehicle", "vehicles", "automobile", "car", "cars", "truck", "trucks",
    "engine", "transmission", "brakes", "horsepower", "mileage", "dealership", "tires",
    "sedan", "suv", "motorcycle", "drivetrain"
}

UNRELATED_FINANCIAL_KEYWORDS = {
    "mortgage", "interest rate", "cryptocurrency", "blockchain", "fintech", "credit card",
    "loan", "loans", "portfolio management", "wealth management", "securities", "brokerage",
    "banking", "hedge fund"
}

UNRELATED_TECH_KEYWORDS = {
    "kubernetes", "sql database", "microservice", "devops", "cloud hosting", "api gateway"
}


class BrandRelevance(StrEnum):
    RELEVANT = "relevant"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    UNRELATED = "unrelated"


@dataclass
class RelevanceAssessment:
    status: BrandRelevance
    reason_code: str | None
    explanation: str
    recommendation: str | None


def _extract_brand_tokens(knowledge: BrandKnowledge) -> set[str]:
    """Extracts substantive tokens from guidelines, facts and terms."""
    stop_words = {
        "this", "that", "with", "from", "your", "have", "been", "must", "will", "more",
        "some", "such", "than", "then", "into", "only", "also", "when", "what", "which",
        "about", "after", "other", "their", "there", "these", "those", "would", "could",
        "should", "brand", "approved", "statement", "information", "guideline", "guidelines"
    }
    tokens: set[str] = set()
    for f in knowledge.facts:
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", f.statement.lower()):
            if word not in stop_words:
                tokens.add(word)
    for g in knowledge.guidelines:
        for word in re.findall(r"\b[a-zA-Z]{4,}\b", g.text.lower()):
            if word not in stop_words:
                tokens.add(word)
    for t in knowledge.terms:
        if t.preferred_term:
            for word in re.findall(r"\b[a-zA-Z]{4,}\b", t.preferred_term.lower()):
                if word not in stop_words:
                    tokens.add(word)
    return tokens


def assess_brand_relevance(
    content: str,
    knowledge: BrandKnowledge,
    title: str | None = None,
    content_type: str | None = None,
) -> RelevanceAssessment:
    """Evaluates brand relevance of submitted content against active brand knowledge.

    Returns:
        RelevanceAssessment with status (RELEVANT, INSUFFICIENT_CONTEXT, UNRELATED).
    """
    brand_name = knowledge.brand_name.strip()
    brand_re = re.compile(rf"\b{re.escape(brand_name)}\b", re.IGNORECASE)

    combined_text = f"{title or ''} {content}".strip()
    text_lower = combined_text.lower()
    content_words = content.strip().split()
    word_count = len(content_words)

    # 1. Explicit brand mention in title or body -> immediately relevant
    if brand_re.search(content) or (title and brand_re.search(title)):
        return RelevanceAssessment(
            status=BrandRelevance.RELEVANT,
            reason_code=None,
            explanation=f"Explicitly references active brand '{brand_name}'.",
            recommendation=None,
        )

    # 2. Check for active domain / skincare relevance
    has_skincare_domain = any(
        re.search(rf"\b{re.escape(kw)}\b", text_lower) for kw in SKINCARE_KEYWORDS
    )
    brand_tokens = _extract_brand_tokens(knowledge)
    has_brand_tokens = any(
        re.search(rf"\b{re.escape(tok)}\b", text_lower) for tok in brand_tokens
    )

    # 3. Check for preferred terms in content
    has_preferred_term = any(
        t.preferred_term and t.preferred_term.lower() in text_lower
        for t in knowledge.terms
    )

    # 4. If substantive skincare concepts, preferred terms, or brand tokens are present
    if has_skincare_domain or has_preferred_term:
        return RelevanceAssessment(
            status=BrandRelevance.RELEVANT,
            reason_code=None,
            explanation=f"Relates to active brand domain (skincare).",
            recommendation=None,
        )

    # 5. Check for very short / greeting copy (insufficient context)
    if word_count < 3:
        return RelevanceAssessment(
            status=BrandRelevance.INSUFFICIENT_CONTEXT,
            reason_code="INSUFFICIENT_CONTEXT",
            explanation=f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable governance assessment.",
            recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
        )

    if word_count < 12 and not has_brand_tokens:
        return RelevanceAssessment(
            status=BrandRelevance.INSUFFICIENT_CONTEXT,
            reason_code="INSUFFICIENT_CONTEXT",
            explanation=f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable governance assessment.",
            recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
        )

    # 6. Check for distinct unrelated commercial entity or industry
    food_matches = sum(1 for kw in UNRELATED_FOOD_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    auto_matches = sum(1 for kw in UNRELATED_AUTOMOTIVE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    fin_matches = sum(1 for kw in UNRELATED_FINANCIAL_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    tech_matches = sum(1 for kw in UNRELATED_TECH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))

    max_unrelated_matches = max(food_matches, auto_matches, fin_matches, tech_matches)

    # Check for another named company/brand pattern (e.g. "Harvest & Hearth is a contemporary food and beverage brand...")
    other_brand_pattern = re.compile(
        r"\b([A-Z][A-Za-z0-9&'\s]{2,30})\s+(?:is|was|aims to be)\s+a\s+(?:contemporary\s+|modern\s+|leading\s+)?(?:food|beverage|automotive|financial|software|tech|logistics)\s+(?:brand|company|corporation|firm)\b",
        re.IGNORECASE,
    )
    explicit_other_brand = bool(other_brand_pattern.search(content))

    if explicit_other_brand or max_unrelated_matches >= 3:
        return RelevanceAssessment(
            status=BrandRelevance.UNRELATED,
            reason_code="UNRELATED_TO_BRAND",
            explanation=(
                f"The submitted content appears to describe a brand, product category or industry that is unrelated to "
                f"{brand_name}, the currently active skincare brand. Its compliance cannot be reliably assessed against "
                f"{brand_name}'s approved guidelines and product information."
            ),
            recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
        )

    # 7. Fallback for substantive text lacking any identifiable brand or industry context
    return RelevanceAssessment(
        status=BrandRelevance.INSUFFICIENT_CONTEXT,
        reason_code="INSUFFICIENT_CONTEXT",
        explanation=f"Content requires human review: insufficient brand or product context for a reliable compliance assessment against {brand_name}.",
        recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
    )


def make_unrelated_finding(
    content: str,
    knowledge: BrandKnowledge,
) -> FindingDraft:
    """Builds a single FindingDraft documenting that the submission is unrelated to the active brand."""
    brand = knowledge.brand_name.strip()
    preview = content.strip()[:100]
    if len(content.strip()) > 100:
        preview += "..."

    return FindingDraft(
        source=FindingSource.RULE_ENGINE,
        category=FindingCategory.OTHER,
        severity=Severity.HIGH,
        finding_type=FindingType.POTENTIAL_ISSUE,
        original_text=preview,
        start_offset=0,
        end_offset=min(len(content), 100),
        guideline_id=None,
        approved_fact_id=None,
        approved_term_id=None,
        evidence=(
            f"Brand governance requires submitted communications to relate to the active brand ({brand}) "
            "before compliance evaluation against brand guidelines."
        ),
        explanation=(
            f"The submitted content appears to describe a brand, product category or industry that is unrelated to "
            f"{brand}, the currently active skincare brand. Its compliance cannot be reliably assessed against "
            f"{brand}'s approved guidelines and product information."
        ),
        suggestion=f"Submit content relevant to {brand} or provide additional context to clarify its relationship with the active brand.",
        confidence=1.0,
        reference_note="Reason code: UNRELATED_TO_BRAND",
    )


def make_insufficient_context_finding(
    content: str,
    knowledge: BrandKnowledge,
) -> FindingDraft:
    """Builds a single FindingDraft documenting insufficient brand context."""
    clean = content.strip()
    return FindingDraft(
        source=FindingSource.RULE_ENGINE,
        category=FindingCategory.OTHER,
        severity=Severity.MEDIUM,
        finding_type=FindingType.POTENTIAL_ISSUE,
        original_text=clean,
        start_offset=0,
        end_offset=len(content),
        guideline_id=None,
        approved_fact_id=None,
        approved_term_id=None,
        evidence="Brand governance requires sufficient communication context to evaluate compliance against approved brand standards.",
        explanation=(
            f"Submitted content ('{clean}') provides insufficient brand or product context for a reliable "
            "governance assessment. Short, greeting, or generic copy requires human review before approval."
        ),
        suggestion="Provide substantive communication copy including relevant brand messaging or product context.",
        confidence=0.95,
        reference_note=None,
    )
