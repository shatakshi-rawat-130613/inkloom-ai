"""Brand relevance and universal brand identity assessment service for Inkloom AI.

Evaluates whether submitted content relates to the active brand prior to
applying brand-specific compliance rules and guidelines.

Distinguishes:
1. RELEVANT_TO_BRAND: Content reasonably belongs to the active brand (brand name,
   products, domain, terminology, messaging, or adequate submission context).
2. UNRELATED_TO_BRAND: Content clearly describes or belongs to another brand,
   regardless of whether that brand operates in the same industry (e.g., another
   skincare brand) or a different industry (e.g., food, fintech, apparel, electronics).
3. INSUFFICIENT_CONTEXT: Content lacks sufficient information or substance to
   establish brand relevance (short greetings, generic copy without context).
"""

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Sequence

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import BrandKnowledge, FindingDraft
from app.services.security_scanner import detect_credentials, is_technical_or_configuration_content


class BrandRelevance(StrEnum):
    RELEVANT_TO_BRAND = "relevant_to_brand"
    UNRELATED_TO_BRAND = "unrelated_to_brand"
    INSUFFICIENT_CONTEXT = "insufficient_context"

    # Backward-compatibility aliases
    RELEVANT = "relevant_to_brand"
    UNRELATED = "unrelated_to_brand"


@dataclass
class RelevanceAssessment:
    status: BrandRelevance
    reason_code: str | None
    explanation: str
    recommendation: str | None
    detected_brand: str | None = None


# Patterns to detect alternative brand names and organizational identity declarations
# Note: use [A-Za-z0-9&' ] rather than \s so matches cannot span across newlines
HEADER_BRAND_PATTERNS = [
    re.compile(
        r"^(?:#+[ \t]*)?([A-Z][A-Za-z0-9&' ]{1,30}?)(?:[ \t]*:[ \t]*|[ \t]+[–\-—][ \t]+)(?:Brand\b|Business\b|Overview\b|Guidelines\b|Style\b|Voice\b|Identity\b)",
        re.MULTILINE,
    ),
    re.compile(
        r"^#+[ \t]*([A-Z][A-Za-z0-9&' ]{1,30}?)(?:[ \t]+Brand\s+Guidelines|[ \t]+Brand\s+Overview|[ \t]+Overview|[ \t]+Skincare|[ \t]+Apparel|[ \t]+Electronics|[ \t]+Travel|[ \t]+Systems)?[ \t]*$",
        re.MULTILINE,
    ),
]

BODY_BRAND_PATTERNS = [
    re.compile(
        r"\b([A-Z][A-Za-z0-9&' ]{1,30}?)[ \t]+(?:is|was|aims to be|has been)[ \t]+(?:a|an|the)[ \t]+(?:[a-z\-]+[ \t]+){0,4}(?:brand|company|corporation|firm|startup|enterprise|label|studio|business|platform|service|provider|maker|manufacturer|app|retailer|collective|line|initiative)\b"
    ),
    re.compile(r"\b(?:At|About)[ \t]+([A-Z][A-Za-z0-9&' ]{1,30}?),?[ \t]+(?:we\b|our\b)"),
    re.compile(
        r"\b([A-Z][A-Za-z0-9&' ]{1,30}?)('s|[ \t]+)(?:mission|vision|core values|values|purpose|story|philosophy|personality|tone of voice|promise|portfolio|team)\b"
    ),
    re.compile(
        r"\b([A-Z][A-Za-z0-9&' ]{1,30}?)[ \t]+(?:offers|provides|develops|creates|manufactures|produces|sells|delivers|specializes in|designs)[ \t]+(?:a|an|the|its|several|[a-z\-]+)\b"
    ),
    re.compile(
        r"\b([A-Z][A-Za-z0-9&' ]{1,30}?)[ \t]+(?:serves|empowers|focuses on|believes that|combines)[ \t]+(?:customers|clients|users|individuals|families|young|familiar|modern)\b"
    ),
]

BRAND_NAME_TOKEN = r"[A-Z][A-Za-z0-9]*(?:[&\'\-\.][A-Za-z0-9]+)*(?:[ \t]+[A-Z][A-Za-z0-9]*(?:[&\'\-\.][A-Za-z0-9]+)*){0,3}"

COMPETITOR_BRAND_PATTERNS = [
    re.compile(
        rf"\b(?:compare|comparing|comparison between|between)\s+({BRAND_NAME_TOKEN})\s+and\s+({BRAND_NAME_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({BRAND_NAME_TOKEN})\s+(?:versus|vs\.?)\s+({BRAND_NAME_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:competitor|competing brand|competing label|competing company|alternative brand|competing skincare brand),?[ \t]+({BRAND_NAME_TOKEN})\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({BRAND_NAME_TOKEN})(?:,?[ \t]+a[ \t]+competing[ \t]+(?:[a-z\-]+[ \t]+)?brand|[ \t]+is[ \t]+a[ \t]+competing[ \t]+(?:[a-z\-]+[ \t]+)?brand)\b",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b({BRAND_NAME_TOKEN})[ \t]+(?:claims?|guarantees?|promises?)[ \t]+(?:results|that|its|an?|to)\b"
    ),
]

GENERIC_IGNORE_WORDS = {
    "about", "the", "brand", "overview", "this", "our", "our team", "our company",
    "the company", "the brand", "the platform", "we", "guidelines", "tone of voice",
    "mission", "vision", "values", "product", "products", "core values", "target audience",
    "brand guidelines", "brand overview", "business identity", "brand personality",
    "product portfolio", "approved", "statement", "skincare", "skincare routine", "all marketing",
    "experience a", "discover a", "make your", "enjoy a", "our cream", "individual product",
    "promotional messages", "these phrases", "examples of", "preferred brand",
    "market", "report", "market report", "brief", "analysis", "review", "summary",
    "in response", "in contrast", "by contrast", "meanwhile", "furthermore",
    "consumer", "consumers", "customer", "customers", "industry"
}

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

UNRELATED_FINTECH_KEYWORDS = {
    "fintech", "financial", "banking", "budgeting", "spending", "transactions",
    "payment", "payments", "digital payment", "credit card", "mortgage", "loans",
    "interest rate", "account management", "savings plans", "cryptocurrency", "blockchain",
    "wealth management", "brokerage", "securities"
}

UNRELATED_ELECTRONICS_KEYWORDS = {
    "electronics", "headphones", "earbuds", "audio", "bluetooth", "battery life",
    "wireless", "hardware", "processor", "display screen", "noise cancelling",
    "speakers", "hifi", "sound quality"
}

UNRELATED_APPAREL_KEYWORDS = {
    "clothing", "apparel", "outerwear", "knitwear", "jacket", "jackets", "trousers",
    "pants", "t-shirt", "garments", "fabrics", "wardrobe", "footwear", "sneakers",
    "merino wool", "textile"
}

UNRELATED_AUTOMOTIVE_KEYWORDS = {
    "automotive", "vehicle", "vehicles", "automobile", "car", "cars", "truck", "trucks",
    "engine", "transmission", "brakes", "horsepower", "mileage", "dealership", "tires",
    "sedan", "suv", "motorcycle", "drivetrain"
}

COMPARATIVE_MARKERS = {
    "vs", "versus", "compared to", "in contrast", "in comparison", "alternative to",
    "competing", "competitor", "competitors", "both brands", "market analysis",
    "industry comparison", "unlike", "market share", "comparing the two",
    "comparison", "in contrast to", "other brands", "competing brand", "competing brands"
}


def _is_valid_brand_candidate(candidate: str, active_lower: str) -> bool:
    if not candidate or "\n" in candidate or "\r" in candidate:
        return False
    clean = candidate.strip().strip("'\"#*-_")
    c_lower = clean.lower()
    if c_lower == active_lower:
        return False
    if active_lower in c_lower:
        return False
    if len(clean.split()) > 4:
        return False
    if c_lower in GENERIC_IGNORE_WORDS:
        return False
    if any(c_lower.startswith(w) for w in ("the ", "this ", "our ", "about ", "every ", "all ")):
        return False
    return True


def detect_alternative_brand(
    text: str,
    active_brand: str,
    title: str | None = None,
) -> str | None:
    """Extracts a distinct alternative brand name if the content establishes one."""
    active_lower = active_brand.lower()
    combined = f"{title or ''}\n{text}".strip()

    # 1. Check title/heading patterns first
    for pat in HEADER_BRAND_PATTERNS:
        for m in pat.finditer(combined):
            candidate = m.group(1).strip()
            if _is_valid_brand_candidate(candidate, active_lower):
                return candidate

    # 2. Check body brand introduction patterns
    for pat in BODY_BRAND_PATTERNS:
        for m in pat.finditer(combined):
            candidate = m.group(1).strip()
            if _is_valid_brand_candidate(candidate, active_lower):
                return candidate

    # 3. Check competitor comparison patterns
    for pat in COMPETITOR_BRAND_PATTERNS:
        for m in pat.finditer(combined):
            for candidate in m.groups():
                if candidate and _is_valid_brand_candidate(candidate.strip(), active_lower):
                    return candidate.strip()

    return None


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
    """Evaluates whether submitted content relates to the active brand.

    Distinguishes:
    - RELEVANT_TO_BRAND: Content reasonably belongs to or meaningfully discusses
      the active brand (including competitor comparisons, market analysis, or product copy).
    - UNRELATED_TO_BRAND: Content exclusively describes or belongs to another brand,
      or primarily covers an unrelated industry with only incidental/zero active brand connection.
    - INSUFFICIENT_CONTEXT: Content lacks sufficient information or substance to
      establish brand relevance (short greetings, generic copy, ambiguous multi-brand mentions).
    """
    brand_name = knowledge.brand_name.strip()
    brand_re = re.compile(rf"\b{re.escape(brand_name)}\b", re.IGNORECASE)

    combined_text = f"{title or ''}\n{content}".strip()
    text_lower = combined_text.lower()
    content_words = content.strip().split()
    word_count = len(content_words)

    # Count active brand mentions in submitted content and title
    brand_mentions = len(brand_re.findall(combined_text))

    # Detect alternative brand candidate
    detected_other = detect_alternative_brand(content, brand_name, title=title)

    # Domain and commercial sector counters
    food_count = sum(1 for kw in UNRELATED_FOOD_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    fin_count = sum(1 for kw in UNRELATED_FINTECH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    elec_count = sum(1 for kw in UNRELATED_ELECTRONICS_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    app_count = sum(1 for kw in UNRELATED_APPAREL_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    auto_count = sum(1 for kw in UNRELATED_AUTOMOTIVE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    max_unrelated = max(food_count, fin_count, elec_count, app_count, auto_count)

    skincare_count = sum(1 for kw in SKINCARE_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower))
    has_skincare_domain = skincare_count > 0

    has_preferred_term = any(
        t.preferred_term and t.preferred_term.lower() in text_lower
        for t in knowledge.terms
    )
    brand_tokens = _extract_brand_tokens(knowledge)
    token_matches = sum(1 for tok in brand_tokens if re.search(rf"\b{re.escape(tok)}\b", text_lower))
    has_comparative_framing = any(re.search(rf"\b{re.escape(m)}\b", text_lower) for m in COMPARATIVE_MARKERS)

    # 0. Detect sensitive credentials (API keys, OAuth secrets, passwords)
    cred_matches = detect_credentials(combined_text)
    if cred_matches:
        return RelevanceAssessment(
            status=BrandRelevance.UNRELATED_TO_BRAND,
            reason_code="SENSITIVE_CREDENTIALS_DETECTED",
            explanation="SECURITY ALERT: Apparent sensitive credentials, API keys, or OAuth secrets detected in submitted content. Technical configuration and secrets cannot be evaluated as brand marketing copy.",
            recommendation="Remove all sensitive credentials and secrets from the submission. Revoke and rotate any exposed keys immediately.",
        )

    # -------------------------------------------------------------
    # CASE 1: ACTIVE BRAND IS NOT MENTIONED (brand_mentions == 0)
    # -------------------------------------------------------------
    if brand_mentions == 0:
        # 1.05 Technical configuration or code content -> UNRELATED_TO_BRAND (not greeting)
        if is_technical_or_configuration_content(content):
            return RelevanceAssessment(
                status=BrandRelevance.UNRELATED_TO_BRAND,
                reason_code="TECHNICAL_CONFIGURATION_CONTENT",
                explanation=(
                    f"The submitted content consists of technical configuration, source code, or system data and does not constitute "
                    f"brand marketing or communication copy. Its compliance cannot be evaluated against {brand_name}'s approved brand guidelines."
                ),
                recommendation=f"Submit customer-facing marketing, promotional, or brand communication copy intended for {brand_name}.",
                detected_brand=None,
            )
        # 1.1 An alternative brand is declared/introduced -> UNRELATED
        if detected_other:
            return RelevanceAssessment(
                status=BrandRelevance.UNRELATED_TO_BRAND,
                reason_code="UNRELATED_TO_BRAND",
                explanation=(
                    f"The submitted content appears to belong to a different brand ('{detected_other}') and is "
                    f"unrelated to {brand_name}. Its compliance cannot be evaluated against {brand_name}'s "
                    f"approved guidelines and product information."
                ),
                recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
                detected_brand=detected_other,
            )

        # 1.2 Unrelated commercial sectors without skincare domain -> UNRELATED
        if max_unrelated >= 3 and not has_skincare_domain:
            return RelevanceAssessment(
                status=BrandRelevance.UNRELATED_TO_BRAND,
                reason_code="UNRELATED_TO_BRAND",
                explanation=(
                    f"The submitted content appears to describe a product category or industry that is unrelated to "
                    f"{brand_name}, the currently active skincare brand. Its compliance cannot be reliably assessed against "
                    f"{brand_name}'s approved guidelines and product information."
                ),
                recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
                detected_brand=None,
            )

        # 1.3 Active brand domain or preferred terms present without explicit brand name -> RELEVANT
        if has_skincare_domain or has_preferred_term:
            return RelevanceAssessment(
                status=BrandRelevance.RELEVANT_TO_BRAND,
                reason_code=None,
                explanation="Relates to active brand domain (skincare).",
                recommendation=None,
            )

        # 1.4 Short or greeting copy -> INSUFFICIENT_CONTEXT
        if word_count < 3:
            return RelevanceAssessment(
                status=BrandRelevance.INSUFFICIENT_CONTEXT,
                reason_code="INSUFFICIENT_CONTEXT",
                explanation=f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable governance assessment.",
                recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
            )

        if word_count < 12 and token_matches == 0:
            return RelevanceAssessment(
                status=BrandRelevance.INSUFFICIENT_CONTEXT,
                reason_code="INSUFFICIENT_CONTEXT",
                explanation=f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable governance assessment.",
                recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
            )

        # Fallback without brand presence -> INSUFFICIENT_CONTEXT
        return RelevanceAssessment(
            status=BrandRelevance.INSUFFICIENT_CONTEXT,
            reason_code="INSUFFICIENT_CONTEXT",
            explanation=f"Content requires human review: insufficient brand or product context for a reliable compliance assessment against {brand_name}.",
            recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
        )

    # -------------------------------------------------------------
    # CASE 2: ACTIVE BRAND IS MENTIONED (brand_mentions > 0)
    # -------------------------------------------------------------
    # 2.05 Technical configuration or code content even if brand is mentioned in string/code
    if is_technical_or_configuration_content(content) and not (has_skincare_domain or has_preferred_term):
        return RelevanceAssessment(
            status=BrandRelevance.UNRELATED_TO_BRAND,
            reason_code="TECHNICAL_CONFIGURATION_CONTENT",
            explanation=(
                f"The submitted content consists of technical configuration, source code, or system data and does not constitute "
                f"brand marketing or communication copy. Its compliance cannot be evaluated against {brand_name}'s approved brand guidelines."
            ),
            recommendation=f"Submit customer-facing marketing, promotional, or brand communication copy intended for {brand_name}.",
            detected_brand=None,
        )
    # 2.1 Incidental mention in an unrelated commercial article:
    # If the text is overwhelmingly about an unrelated industry (e.g. automotive, fintech, food)
    # with no skincare substance and active brand is mentioned only once in passing.
    if max_unrelated >= 3 and not has_skincare_domain and not has_preferred_term and brand_mentions <= 1:
        return RelevanceAssessment(
            status=BrandRelevance.UNRELATED_TO_BRAND,
            reason_code="UNRELATED_TO_BRAND",
            explanation=(
                f"The submitted content primarily describes an unrelated product category or industry "
                f"('{detected_other or 'unrelated industry'}'). While {brand_name} is mentioned in passing, "
                f"the content lacks substantive connection to {brand_name}'s products, formulations, or brand guidelines."
            ),
            recommendation=f"Submit content relevant to {brand_name} or provide additional context to clarify its relationship with the active brand.",
            detected_brand=detected_other,
        )

    # 2.2 If an alternative brand is also detected (Competitor comparison / multi-brand context):
    if detected_other:
        # Check if active brand has meaningful substance or contextual connection
        has_meaningful_connection = (
            has_skincare_domain
            or has_preferred_term
            or has_comparative_framing
            or brand_mentions >= 2
            or token_matches >= 2
        )
        if has_meaningful_connection:
            return RelevanceAssessment(
                status=BrandRelevance.RELEVANT_TO_BRAND,
                reason_code=None,
                explanation=(
                    f"The submitted content discusses active brand '{brand_name}' in comparison with or relation to "
                    f"another entity ('{detected_other}'). Active brand context is established."
                ),
                recommendation=None,
                detected_brand=detected_other,
            )

        # If both are mentioned but text is very short or ambiguous without substance
        if word_count < 12:
            return RelevanceAssessment(
                status=BrandRelevance.INSUFFICIENT_CONTEXT,
                reason_code="INSUFFICIENT_CONTEXT",
                explanation=(
                    f"Submitted content mentions both {brand_name} and '{detected_other}', but provides insufficient "
                    "context to establish clear brand governance relevance."
                ),
                recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
                detected_brand=detected_other,
            )

    # 2.3 Single word or very short copy with brand name but no other context
    if word_count < 3 and not (has_skincare_domain or has_preferred_term):
        return RelevanceAssessment(
            status=BrandRelevance.INSUFFICIENT_CONTEXT,
            reason_code="INSUFFICIENT_CONTEXT",
            explanation=f"Submitted content ('{content.strip()}') provides insufficient brand or product context for a reliable governance assessment.",
            recommendation="Provide substantive communication copy including relevant brand messaging or product context.",
        )

    # 2.4 Substantive active brand copy
    return RelevanceAssessment(
        status=BrandRelevance.RELEVANT_TO_BRAND,
        reason_code=None,
        explanation=f"Explicitly references active brand '{brand_name}'.",
        recommendation=None,
        detected_brand=detected_other,
    )


def make_unrelated_finding(
    content: str,
    knowledge: BrandKnowledge,
    detected_brand: str | None = None,
) -> FindingDraft:
    """Builds a single FindingDraft documenting that the submission is unrelated to the active brand."""
    brand = knowledge.brand_name.strip()
    preview = content.strip()[:100]
    if len(content.strip()) > 100:
        preview += "..."

    if detected_brand:
        explanation = (
            f"The submitted content appears to belong to a different brand ('{detected_brand}') and is "
            f"unrelated to {brand}. Its compliance cannot be evaluated against {brand}'s approved "
            "guidelines, facts and product information."
        )
    else:
        explanation = (
            f"The submitted content appears to describe a brand, product category or industry that is unrelated to "
            f"{brand}, the currently active skincare brand. Its compliance cannot be reliably assessed against "
            f"{brand}'s approved guidelines and product information."
        )

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
            f"Brand governance requires submitted communications to belong to the active brand ({brand}) "
            "before compliance evaluation against brand guidelines."
        ),
        explanation=explanation,
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
