"""Regression tests for secure configuration validation and demo seed requirements.

Verifies:
1. DEMO_SEED_PASSWORD is required when seeding demo accounts and fails cleanly when missing.
2. Insecure or static default JWT_SECRET_KEY values are strictly rejected in production.
3. Safe per-process random secrets are generated in local development.
"""

import os
import pytest
from unittest.mock import patch

from app.config import Settings, get_settings, KNOWN_INSECURE_JWT_SECRETS
from app.seed import get_seed_password, seed_demo_data


def test_missing_demo_seed_password_raises_clear_error(monkeypatch):
    """When DEMO_SEED_PASSWORD is unset or empty, get_seed_password must fail with a clear error and never leak secrets."""
    monkeypatch.setenv("DEMO_SEED_PASSWORD", "")
    get_settings.cache_clear()

    with pytest.raises(ValueError) as exc_info:
        get_seed_password()

    msg = str(exc_info.value)
    assert "DEMO_SEED_PASSWORD" in msg
    assert "explicitly provided" in msg
    # Ensure no secret strings or passwords appear in error message
    assert "LumaCareDemo2026!" not in msg


def test_seed_demo_data_fails_without_demo_seed_password(db, monkeypatch):
    """Calling seed_demo_data without DEMO_SEED_PASSWORD must raise ValueError."""
    monkeypatch.setenv("DEMO_SEED_PASSWORD", "")
    get_settings.cache_clear()

    with pytest.raises(ValueError) as exc_info:
        seed_demo_data(db)

    assert "DEMO_SEED_PASSWORD" in str(exc_info.value)


def test_production_jwt_secret_required():
    """In production, omitting JWT_SECRET_KEY must raise ValueError."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key="",
            database_url="sqlite:///./test.db",
        )
    assert "JWT_SECRET_KEY is required in production" in str(exc_info.value)


def test_production_rejects_known_insecure_defaults():
    """In production, known development default secrets must be explicitly rejected."""
    for insecure_key in KNOWN_INSECURE_JWT_SECRETS:
        with pytest.raises(ValueError) as exc_info:
            Settings(
                environment="production",
                jwt_secret_key=insecure_key,
                database_url="sqlite:///./test.db",
            )
        assert "Known insecure development JWT_SECRET_KEY detected in production" in str(exc_info.value)


def test_production_rejects_short_jwt_secrets():
    """In production, secrets under 32 characters must be rejected."""
    with pytest.raises(ValueError) as exc_info:
        Settings(
            environment="production",
            jwt_secret_key="too-short-secret-123",
            database_url="sqlite:///./test.db",
        )
    assert "must be at least 32 characters long" in str(exc_info.value)


def test_production_accepts_strong_secret():
    """In production, an independently generated secret >= 32 characters is accepted."""
    strong_key = "a" * 32
    cfg = Settings(
        environment="production",
        jwt_secret_key=strong_key,
        database_url="sqlite:///./test.db",
    )
    assert cfg.jwt_secret_key == strong_key
    assert cfg.is_production is True


def test_development_fallback_generates_safe_random_secret():
    """In development, an unset JWT_SECRET_KEY automatically generates a safe random secret."""
    cfg = Settings(
        environment="development",
        jwt_secret_key="",
        database_url="sqlite:///./test.db",
    )
    assert len(cfg.jwt_secret_key) >= 32
    assert cfg.jwt_secret_key not in KNOWN_INSECURE_JWT_SECRETS
    assert cfg.is_production is False
