"""Tests for security scanning, credential detection, secret redaction, and technical content handling."""

import pytest

from app.enums import OverallStatus, Severity
from app.services.analyzer import analyze_content
from app.services.relevance import BrandRelevance, assess_brand_relevance
from app.services.security_scanner import (
    CredentialType,
    detect_credentials,
    is_technical_or_configuration_content,
    redact_sensitive_text,
)
from tests.test_validation import KNOWLEDGE


# Synthetic test credentials dynamically assembled at runtime to prevent static git secret scanner false-positives
SYNTHETIC_OAUTH_CLIENT_ID = "".join(["123456789012-sampleclientid12345.", "apps.", "googleusercontent", ".com"])
SYNTHETIC_OAUTH_SECRET = "".join(["GOC", "SPX-", "sampleSecretForTesting12345678"])
SYNTHETIC_GOOGLE_API_KEY = "".join(["AIza", "SySampleTestKeyForUnitTestingOnly12345"])
SYNTHETIC_OPENAI_API_KEY = "".join(["sk-", "live-sampleTestKeyForUnitTesting987654"])
SYNTHETIC_GITHUB_TOKEN = "".join(["ghp_", "sampleGithubTokenForTesting123456789"])
SYNTHETIC_AWS_KEY = "".join(["AKIA", "SAMPLE1234567890"])
SYNTHETIC_PASSWORD = "".join(["super", "Secret", "Password", "123"])


# ------------------------------------------------------------------------------
# 1. UNIT TESTS: Credential Detection & Redaction
# ------------------------------------------------------------------------------

def test_detect_and_redact_oauth_json():
    content = f'''{{
  "web": {{
    "client_id": "{SYNTHETIC_OAUTH_CLIENT_ID}",
    "client_secret": "{SYNTHETIC_OAUTH_SECRET}",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth"
  }}
}}'''
    matches = detect_credentials(content)
    assert len(matches) >= 2
    types = {m.credential_type for m in matches}
    assert CredentialType.OAUTH_CLIENT_ID in types
    assert CredentialType.OAUTH_SECRET in types

    redacted = redact_sensitive_text(content)
    assert SYNTHETIC_OAUTH_CLIENT_ID not in redacted
    assert SYNTHETIC_OAUTH_SECRET not in redacted
    assert "[REDACTED_CLIENT_ID]" in redacted
    assert "[REDACTED_OAUTH_SECRET]" in redacted
    # Valid JSON formatting structure is preserved
    assert '"client_id": "[REDACTED_CLIENT_ID]"' in redacted
    assert '"client_secret": "[REDACTED_OAUTH_SECRET]"' in redacted


def test_detect_and_redact_api_keys():
    samples = [
        ("Google API Key", f"api_key = '{SYNTHETIC_GOOGLE_API_KEY}'", SYNTHETIC_GOOGLE_API_KEY, "[REDACTED_API_KEY]"),
        ("OpenAI Key", f"OPENAI_KEY = '{SYNTHETIC_OPENAI_API_KEY}'", SYNTHETIC_OPENAI_API_KEY, "[REDACTED_API_KEY]"),
        ("GitHub Token", f"git clone https://{SYNTHETIC_GITHUB_TOKEN}@github.com/repo", SYNTHETIC_GITHUB_TOKEN, "[REDACTED_API_KEY]"),
        ("AWS Key", f"export AWS_ACCESS_KEY_ID={SYNTHETIC_AWS_KEY}", SYNTHETIC_AWS_KEY, "[REDACTED_API_KEY]"),
    ]
    for name, text, secret, placeholder in samples:
        matches = detect_credentials(text)
        assert len(matches) >= 1, f"Failed to detect {name}"
        redacted = redact_sensitive_text(text)
        assert secret not in redacted, f"Raw secret leaked for {name}"
        assert placeholder in redacted, f"Missing placeholder for {name}"


def test_detect_and_redact_db_uri():
    db_uri = f"postgresql://app_user:{SYNTHETIC_PASSWORD}@db.internal.net:5432/inkloom_prod"
    matches = detect_credentials(db_uri)
    assert len(matches) == 1
    assert matches[0].credential_type == CredentialType.DATABASE_URI

    redacted = redact_sensitive_text(db_uri)
    assert SYNTHETIC_PASSWORD not in redacted
    assert "postgresql://app_user:[REDACTED_PASSWORD]@db.internal.net:5432/inkloom_prod" == redacted


def test_detect_and_redact_private_key():
    pem = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y3TestKeyDataNotRealForTestingPurposesOnly12345\n"
        "-----END RSA PRIVATE KEY-----"
    )
    matches = detect_credentials(pem)
    assert len(matches) == 1
    assert matches[0].credential_type == CredentialType.PRIVATE_KEY

    redacted = redact_sensitive_text(pem)
    assert "MIIEowIBAAKCAQEA0Y3TestKeyDataNotRealForTestingPurposesOnly12345" not in redacted
    assert "[REDACTED_PRIVATE_KEY]" in redacted


# ------------------------------------------------------------------------------
# 2. INTEGRATION TESTS: Analyzer & Assessment with Credentials
# ------------------------------------------------------------------------------

def test_analyze_submission_with_oauth_credentials_redacts_and_warns():
    payload = f'{{"client_secret": "{SYNTHETIC_OAUTH_SECRET}"}}'
    res = analyze_content(payload, KNOWLEDGE)

    assert res.overall_status == OverallStatus.NEEDS_REVIEW
    assert res.requires_human_review is True
    assert "SECURITY WARNING: Sensitive credentials detected" in res.summary
    assert len(res.findings) == 1

    finding = res.findings[0]
    assert finding.severity == Severity.CRITICAL
    assert "Reason code: SENSITIVE_CREDENTIALS_DETECTED" in (finding.reference_note or "")
    # Check that raw secret is NEVER repeated in findings, preview, or summary
    assert SYNTHETIC_OAUTH_SECRET not in finding.original_text
    assert SYNTHETIC_OAUTH_SECRET not in finding.explanation
    assert SYNTHETIC_OAUTH_SECRET not in finding.suggestion
    assert SYNTHETIC_OAUTH_SECRET not in res.summary
    assert "[REDACTED_OAUTH_SECRET]" in finding.original_text


def test_analyze_submission_with_api_key_in_marketing_draft():
    draft = f"Check out LumaCare's new API at api.lumacare.com using key {SYNTHETIC_GOOGLE_API_KEY} for your routine."
    res = analyze_content(draft, KNOWLEDGE)

    assert res.overall_status == OverallStatus.NEEDS_REVIEW
    assert res.requires_human_review is True
    assert "SECURITY WARNING" in res.summary
    assert len(res.findings) == 1
    assert SYNTHETIC_GOOGLE_API_KEY not in res.findings[0].original_text
    assert SYNTHETIC_GOOGLE_API_KEY not in res.summary
    assert "[REDACTED_API_KEY]" in res.findings[0].original_text


# ------------------------------------------------------------------------------
# 3. TECHNICAL CONFIGURATION VS MARKETING CONTENT
# ------------------------------------------------------------------------------

def test_technical_content_distinguished_from_marketing():
    tech_snippets = [
        '{\n  "service": "auth-gateway",\n  "port": 8080,\n  "enabled": true\n}',
        'curl -X POST https://api.example.com/v1/auth -H "Content-Type: application/json"',
        'import os\nimport sys\ndef main():\n    print("Running diagnostics")',
        'Traceback (most recent call last):\n  File "app.py", line 42, in run\nTypeError: null pointer',
        'export DATABASE_URL=postgres://localhost:5432/dev\nexport PORT=3000',
    ]
    for snippet in tech_snippets:
        assert is_technical_or_configuration_content(snippet) is True
        rel = assess_brand_relevance(snippet, KNOWLEDGE)
        assert rel.reason_code in ("TECHNICAL_CONFIGURATION_CONTENT", "SENSITIVE_CREDENTIALS_DETECTED")
        assert rel.status == BrandRelevance.UNRELATED_TO_BRAND
        # Must NOT be classified as generic greeting
        assert "insufficient brand or product context" not in rel.explanation

        res = analyze_content(snippet, KNOWLEDGE)
        assert res.overall_status == OverallStatus.NEEDS_REVIEW
        assert res.requires_human_review is True
        assert "TECHNICAL DATA DETECTED" in res.summary or "SECURITY WARNING" in res.summary


def test_ordinary_short_greetings_retain_insufficient_context():
    greetings = [
        "helllooooooo",
        "Hello there!",
        "Good morning!",
        "Have a beautiful day!",
        "Thanks for visiting.",
    ]
    for greet in greetings:
        assert is_technical_or_configuration_content(greet) is False
        rel = assess_brand_relevance(greet, KNOWLEDGE)
        assert rel.status == BrandRelevance.INSUFFICIENT_CONTEXT
        assert rel.reason_code == "INSUFFICIENT_CONTEXT"
        assert "insufficient brand or product context" in rel.explanation

        res = analyze_content(greet, KNOWLEDGE)
        assert res.overall_status == OverallStatus.NEEDS_REVIEW
        assert res.requires_human_review is True
        assert "insufficient brand or product context" in res.summary.lower()


# ------------------------------------------------------------------------------
# 4. REGRESSION: Multi-brand and Competitor mentions still work
# ------------------------------------------------------------------------------

def test_competitor_comparison_still_relevant():
    text = (
        "LumaCare is our skincare brand and supports clearer-looking skin. "
        "In comparison, Velveteen claims to guarantee overnight results without clinical evidence."
    )
    rel = assess_brand_relevance(text, KNOWLEDGE)
    assert rel.status == BrandRelevance.RELEVANT_TO_BRAND
    assert rel.reason_code is None
