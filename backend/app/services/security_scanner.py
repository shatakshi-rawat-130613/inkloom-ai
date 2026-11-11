"""Security and credential scanner for Inkloom AI.

Detects sensitive credentials, OAuth secrets, API keys, passwords, and technical/configuration
content. Redacts all sensitive values to prevent credential leakage in findings, logs,
reasoning, and UI previews.
"""

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Sequence

from app.enums import FindingCategory, FindingSource, FindingType, Severity
from app.schemas import BrandKnowledge, FindingDraft


class CredentialType(StrEnum):
    OAUTH_SECRET = "OAuth Client Secret"
    OAUTH_CLIENT_ID = "OAuth Client ID"
    API_KEY = "API Key"
    PASSWORD = "Password"
    PRIVATE_KEY = "Private Key"
    JWT_TOKEN = "JSON Web Token (JWT)"
    DATABASE_URI = "Database Connection String with Credentials"
    SECRET_TOKEN = "Secret Token / Key"


@dataclass
class CredentialMatch:
    credential_type: CredentialType
    raw_match: str
    secret_value: str
    redacted_snippet: str
    start: int
    end: int


# ------------------------------------------------------------------------------
# CREDENTIAL DETECTION PATTERNS
# ------------------------------------------------------------------------------

# 1. OAuth Client Secret patterns
OAUTH_SECRET_PATTERNS = [
    re.compile(r"(?i)[\"']?\b(client_secret|clientsecret|oauth_secret)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.~]{10,})[\"']?"),
    re.compile(r"(?i)\b(GOCSPX-[A-Za-z0-9_\-]{24,})\b"),
]

# 2. OAuth Client ID patterns
OAUTH_CLIENT_ID_PATTERNS = [
    re.compile(r"(?i)[\"']?\b(client_id|clientid)[\"']?\s*[:=]\s*[\"']?([0-9]{10,}[a-zA-Z0-9_\-\.]*\.apps\.googleusercontent\.com)[\"']?"),
    re.compile(r"(?i)[\"']?\b(client_id|clientid)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.]{20,})[\"']?"),
]

# 3. Dedicated API Key patterns
API_KEY_PATTERNS = [
    # Google Gemini / Cloud API Key
    re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,45})\b"),
    re.compile(r"\b(AQ\.[0-9A-Za-z\-_]{40,})\b"),
    # OpenAI / Anthropic Key
    re.compile(r"\b(sk-(?:live_|proj_|test_)?[A-Za-z0-9_\-]{20,})\b"),
    # GitHub Token
    re.compile(r"\b((?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,40})\b"),
    re.compile(r"\b(github_pat_[A-Za-z0-9_]{50,})\b"),
    # AWS Access Key
    re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    re.compile(r"(?i)[\"']?\b(aws_secret_access_key|aws_secret_key)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9/+=]{40})[\"']?"),
    # Slack / Stripe Key
    re.compile(r"\b(xox[baprs]-[0-9a-zA-Z-]{10,})\b"),
    re.compile(r"\b(sk_live_[0-9a-zA-Z]{24,})\b"),
]

# 4. Generic credential assignment patterns (password, secret, token, api_key)
GENERIC_CREDENTIAL_PATTERNS = [
    re.compile(r"(?i)[\"']?\b(api_key|apikey|secret_key|private_key|auth_token|token|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?([^\s\"';,]{12,})[\"']?"),
    re.compile(r"(?i)[\"']?\b(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?([^\s\"';,]{8,})[\"']?"),
]

# 5. Private Key blocks
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
)

# 6. Database Connection URIs with embedded passwords
DB_URI_PATTERN = re.compile(
    r"(?i)(?:postgres|postgresql|mysql|mongodb(?:\+srv)?):\/\/([a-zA-Z0-9_\.\-]+):([^@\s\"']+)@([^\s\"']+)"
)

# 7. JWT Tokens
JWT_PATTERN = re.compile(
    r"\b(eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})\b"
)


# ------------------------------------------------------------------------------
# TECHNICAL & CONFIGURATION DETECTION PATTERNS
# ------------------------------------------------------------------------------

TECHNICAL_STRUCTURE_PATTERNS = [
    # JSON payload structure
    re.compile(r"^\s*\{[\s\S]*\"[a-zA-Z0-9_\-]+\"\s*:[\s\S]*\}\s*$", re.MULTILINE),
    # YAML or properties config
    re.compile(r"^[a-zA-Z0-9_\.\-]+:\s+[^\n]+$", re.MULTILINE),
    # Key-value assignments like .env
    re.compile(r"^[A-Z0-9_]{3,}\s*=\s*[^\n]+$", re.MULTILINE),
    # Programming language declarations / imports
    re.compile(r"\b(import\s+[a-zA-Z0-9_\.]+|from\s+[a-zA-Z0-9_\.]+\s+import|def\s+[a-zA-Z0-9_]+\s*\(|function\s+[a-zA-Z0-9_]+\s*\(|const\s+[a-zA-Z0-9_]+\s*=|class\s+[A-Za-z0-9_]+[:\s\{])"),
    # Shell commands and CLI invocations
    re.compile(r"\b(curl\s+-[A-Za-z]|wget\s+http|docker\s+run|npm\s+(?:install|run)|pip\s+install|git\s+(?:clone|commit|push)|export\s+[A-Z_]+=|chmod\s+[0-9]{3})\b"),
    # Stack traces and error dumps
    re.compile(r"(?i)(?:Traceback \(most recent call last\)|NullPointerException|Unhandled exception|at line [0-9]+|SyntaxError:|TypeError:)"),
    # OAuth protocol parameters and endpoints
    re.compile(r"(?i)\b(grant_type=(?:client_credentials|authorization_code|refresh_token)|response_type=code|redirect_uri=|client_secret=|client_id=)"),
]


# ------------------------------------------------------------------------------
# DETECTION & REDACTION LOGIC
# ------------------------------------------------------------------------------

def detect_credentials(text: str) -> list[CredentialMatch]:
    """Scans text for apparent API keys, OAuth secrets, passwords and credentials."""
    matches: list[CredentialMatch] = []
    seen_spans: set[tuple[int, int]] = set()

    # 1. Private keys
    for m in PRIVATE_KEY_PATTERN.finditer(text):
        span = (m.start(), m.end())
        seen_spans.add(span)
        matches.append(
            CredentialMatch(
                credential_type=CredentialType.PRIVATE_KEY,
                raw_match=m.group(0),
                secret_value=m.group(0),
                redacted_snippet="-----BEGIN PRIVATE KEY----- [REDACTED_PRIVATE_KEY] -----END PRIVATE KEY-----",
                start=m.start(),
                end=m.end(),
            )
        )

    # 2. Database connection URIs
    for m in DB_URI_PATTERN.finditer(text):
        pwd = m.group(2)
        span = (m.start(2), m.end(2))
        seen_spans.add(span)
        matches.append(
            CredentialMatch(
                credential_type=CredentialType.DATABASE_URI,
                raw_match=m.group(0),
                secret_value=pwd,
                redacted_snippet="[REDACTED_PASSWORD]",
                start=span[0],
                end=span[1],
            )
        )

    # 3. OAuth client secrets
    for pat in OAUTH_SECRET_PATTERNS:
        for m in pat.finditer(text):
            if len(m.groups()) == 2:
                span = (m.start(2), m.end(2))
                secret = m.group(2)
            else:
                span = (m.start(1), m.end(1))
                secret = m.group(1)
            if any(s[0] <= span[0] and s[1] >= span[1] for s in seen_spans):
                continue
            seen_spans.add(span)
            matches.append(
                CredentialMatch(
                    credential_type=CredentialType.OAUTH_SECRET,
                    raw_match=m.group(0),
                    secret_value=secret,
                    redacted_snippet="[REDACTED_OAUTH_SECRET]",
                    start=span[0],
                    end=span[1],
                )
            )

    # 4. OAuth client IDs
    for pat in OAUTH_CLIENT_ID_PATTERNS:
        for m in pat.finditer(text):
            span = (m.start(2), m.end(2))
            if any(s[0] <= span[0] and s[1] >= span[1] for s in seen_spans):
                continue
            seen_spans.add(span)
            cid = m.group(2)
            matches.append(
                CredentialMatch(
                    credential_type=CredentialType.OAUTH_CLIENT_ID,
                    raw_match=m.group(0),
                    secret_value=cid,
                    redacted_snippet="[REDACTED_CLIENT_ID]",
                    start=span[0],
                    end=span[1],
                )
            )

    # 5. Dedicated API keys
    for pat in API_KEY_PATTERNS:
        for m in pat.finditer(text):
            group_idx = 2 if len(m.groups()) == 2 else (1 if len(m.groups()) == 1 else 0)
            span = (m.start(group_idx), m.end(group_idx))
            if any(s[0] <= span[0] and s[1] >= span[1] for s in seen_spans):
                continue
            seen_spans.add(span)
            secret = m.group(group_idx)
            matches.append(
                CredentialMatch(
                    credential_type=CredentialType.API_KEY,
                    raw_match=m.group(0),
                    secret_value=secret,
                    redacted_snippet="[REDACTED_API_KEY]",
                    start=span[0],
                    end=span[1],
                )
            )

    # 6. Generic credentials & passwords
    for pat in GENERIC_CREDENTIAL_PATTERNS:
        for m in pat.finditer(text):
            span = (m.start(2), m.end(2))
            if any(s[0] <= span[0] and s[1] >= span[1] for s in seen_spans):
                continue
            seen_spans.add(span)
            key_name = m.group(1).lower()
            secret = m.group(2)
            ctype = CredentialType.PASSWORD if "pass" in key_name or "pwd" in key_name else CredentialType.SECRET_TOKEN
            matches.append(
                CredentialMatch(
                    credential_type=ctype,
                    raw_match=m.group(0),
                    secret_value=secret,
                    redacted_snippet=f"[REDACTED_{ctype.name}]",
                    start=span[0],
                    end=span[1],
                )
            )

    # 7. JWT tokens
    for m in JWT_PATTERN.finditer(text):
        span = (m.start(), m.end())
        if any(s[0] <= m.start() and s[1] >= m.end() for s in seen_spans):
            continue
        seen_spans.add(span)
        matches.append(
            CredentialMatch(
                credential_type=CredentialType.JWT_TOKEN,
                raw_match=m.group(0),
                secret_value=m.group(0),
                redacted_snippet="[REDACTED_JWT_TOKEN]",
                start=m.start(),
                end=m.end(),
            )
        )

    return matches


def redact_sensitive_text(text: str) -> str:
    """Redacts all detected sensitive credentials and API keys from a string."""
    matches = detect_credentials(text)
    if not matches:
        return text

    # Sort in reverse order by start offset so replacements don't shift offsets
    sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
    redacted = text
    for m in sorted_matches:
        redacted = redacted[:m.start] + m.redacted_snippet + redacted[m.end:]
    return redacted


def is_technical_or_configuration_content(content: str) -> bool:
    """Distinguishes technical/config/code content from ordinary marketing text or short greetings."""
    clean = content.strip()
    if not clean:
        return False

    # Check for credentials first (if it has credentials, it is technical/security content)
    if detect_credentials(clean):
        return True

    # Check for technical syntax markers
    match_count = 0
    for pat in TECHNICAL_STRUCTURE_PATTERNS:
        if pat.search(clean):
            match_count += 1

    # Check for character distribution typical of code/config ({}, [], ;, =, _)
    tech_chars = sum(1 for c in clean if c in "{}[];:=_\\$<>`|")
    tech_ratio = tech_chars / max(len(clean), 1)

    if match_count >= 1 or tech_ratio > 0.08:
        # Verify it's not just a casual marketing phrase with punctuation
        words = clean.split()
        if len(words) < 20 and (clean.startswith(("{", "[", "curl", "import", "export")) or ":" in clean or "=" in clean):
            return True
        if match_count >= 2:
            return True

    return False


def make_credential_finding(content: str, matches: list[CredentialMatch]) -> FindingDraft:
    """Creates a high-severity security finding documenting sensitive credential detection."""
    types_found = ", ".join(sorted({m.credential_type.value for m in matches}))
    # Build a redacted preview snippet
    redacted_preview = redact_sensitive_text(content.strip()[:180])

    return FindingDraft(
        source=FindingSource.RULE_ENGINE,
        category=FindingCategory.OTHER,
        severity=Severity.CRITICAL,
        finding_type=FindingType.CONFIRMED_RULE_VIOLATION,
        original_text=redacted_preview,
        evidence="Security and brand governance policies strictly prohibit publishing or transmitting credentials, API keys, client secrets, or authentication tokens.",
        explanation=(
            f"SECURITY ALERT: Apparent sensitive credentials ({types_found}) detected in submitted content. "
            f"Content containing client secrets or credentials creates critical security exposure and must not be published."
        ),
        suggestion=(
            "Immediately remove all client secrets, API keys, passwords, and sensitive configuration from the submission. "
            "Revoke and rotate any exposed credentials immediately."
        ),
        confidence=0.99,
        reference_note="Reason code: SENSITIVE_CREDENTIALS_DETECTED",
    )


def make_technical_content_finding(content: str, knowledge: BrandKnowledge) -> FindingDraft:
    """Creates a governance finding documenting that content is technical/config rather than marketing copy."""
    clean_preview = redact_sensitive_text(content.strip()[:180])
    return FindingDraft(
        source=FindingSource.RULE_ENGINE,
        category=FindingCategory.OTHER,
        severity=Severity.HIGH,
        finding_type=FindingType.POTENTIAL_ISSUE,
        original_text=clean_preview,
        evidence=f"Brand governance and compliance rules apply to marketing, customer-facing, and promotional copy for {knowledge.brand_name}.",
        explanation=(
            f"The submitted content consists of technical configuration, source code, or system data and does not constitute "
            f"brand marketing or communication copy. Its compliance cannot be evaluated against {knowledge.brand_name}'s approved brand guidelines."
        ),
        suggestion=(
            f"Submit customer-facing marketing, promotional, or brand communication copy intended for {knowledge.brand_name}."
        ),
        confidence=0.95,
        reference_note="Reason code: TECHNICAL_CONFIGURATION_CONTENT",
    )
