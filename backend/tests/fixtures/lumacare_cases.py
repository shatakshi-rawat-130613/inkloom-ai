"""The three LumaCare regression cases supplied with the project brief.

Used by Phase 2 rule-engine tests (deterministic, always run) and by the
optional live Gemini test (runs only when GEMINI_API_KEY is set).
"""

from dataclasses import dataclass, field

from app.enums import OverallStatus


@dataclass(frozen=True)
class LumaCareCase:
    name: str
    content: str
    expected_status: OverallStatus
    # Phrases that MUST be covered by at least one finding's original_text.
    must_flag: tuple[str, ...] = field(default_factory=tuple)
    # Phrases that must NOT appear in any non-recommendation finding.
    must_not_flag: tuple[str, ...] = field(default_factory=tuple)
    expects_positive_observations: bool = False
    notes: str = ""


NON_COMPLIANT = LumaCareCase(
    name="test_1_non_compliant",
    content=(
        "Our revolutionary cream guarantees 100% acne removal in just 2 days! "
        "Buy now and get flawless skin instantly."
    ),
    expected_status=OverallStatus.NON_COMPLIANT,
    must_flag=("guarantees 100% acne removal", "in just 2 days", "flawless skin instantly"),
    notes="Prohibited terminology (guarantee of acne removal), unsupported timeframe, exaggerated messaging.",
)

COMPLIANT = LumaCareCase(
    name="test_2_compliant",
    content=(
        "Discover a simple addition to your skincare routine with LumaCare. "
        "Our cream is designed to support clearer-looking skin. "
        "Enjoy a gentle, reassuring approach to everyday skincare."
    ),
    expected_status=OverallStatus.COMPLIANT,
    must_not_flag=("support clearer-looking skin", "gentle, reassuring approach"),
    expects_positive_observations=True,
    notes="No unnecessary findings. Preferred terminology and appropriate tone.",
)

PARTIALLY_COMPLIANT = LumaCareCase(
    name="test_3_partially_compliant",
    content=(
        "Make your skincare routine simpler with LumaCare. "
        "Our cream supports clearer-looking skin and helps reduce acne within 7 days. "
        "Experience a gentle approach to everyday skincare."
    ),
    expected_status=OverallStatus.NEEDS_REVIEW,
    must_flag=("helps reduce acne within 7 days",),
    must_not_flag=("supports clearer-looking skin",),
    expects_positive_observations=True,
    notes="Unsupported acne-reduction claim and timeframe; preserve positive observations. Not a direct contradiction.",
)

ALL_CASES = (NON_COMPLIANT, COMPLIANT, PARTIALLY_COMPLIANT)
