"""Shared enumerations. Single source of truth for status and classification values.

Centrally controlled contract file. Mirrored in frontend/src/api/types.ts and
checked by tests/test_contract_parity.py.
"""

from enum import StrEnum


class UserRole(StrEnum):
    EDITOR = "editor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class ContentType(StrEnum):
    SOCIAL_POST = "social_post"
    EMAIL = "email"
    WEB_PAGE = "web_page"
    ADVERTISEMENT = "advertisement"
    PRODUCT_DESCRIPTION = "product_description"
    PRESS_RELEASE = "press_release"
    OTHER = "other"


class SubmissionStatus(StrEnum):
    DRAFT = "draft"
    ANALYZED = "analyzed"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISIONS_REQUESTED = "revisions_requested"


class OverallStatus(StrEnum):
    COMPLIANT = "compliant"
    NEEDS_REVIEW = "needs_review"
    NON_COMPLIANT = "non_compliant"


class FindingType(StrEnum):
    CONFIRMED_RULE_VIOLATION = "confirmed_rule_violation"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    POTENTIAL_ISSUE = "potential_issue"
    RECOMMENDATION = "recommendation"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingCategory(StrEnum):
    TERMINOLOGY = "terminology"
    OUTCOME_CLAIM = "outcome_claim"
    FACTUAL_CONSISTENCY = "factual_consistency"
    TIMEFRAME = "timeframe"
    TONE = "tone"
    OTHER = "other"


class FindingSource(StrEnum):
    RULE_ENGINE = "rule_engine"
    AI = "ai"


class AIStatus(StrEnum):
    OK = "ok"                              # Gemini responded with a valid structured result
    UNAVAILABLE = "unavailable"            # timeout, network or provider error
    INVALID_RESPONSE = "invalid_response"  # response failed Pydantic validation
    DISABLED = "disabled"                  # no API key configured


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISIONS_REQUESTED = "revisions_requested"


class SubmissionAction(StrEnum):
    """Actions the frontend may offer, computed server-side from status."""

    EDIT = "edit"
    ANALYZE = "analyze"
    REQUEST_REVIEW = "request_review"
    REVIEW = "review"


SEVERITY_RANK: dict[Severity, int] = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
    Severity.INFORMATIONAL: 0,
}
