"""Application settings loaded from environment variables.

Centrally controlled contract file. See .env.example for documentation.
"""

import secrets
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Per-process randomly generated secret for safe zero-config local development
_DEV_RANDOM_SECRET = secrets.token_urlsafe(32)

KNOWN_INSECURE_JWT_SECRETS = {
    "inkloom-production-jwt-secret-key-do-not-share-32charsmin",
    "secret",
    "changeme",
    "jwt-secret-key",
    "development-jwt-secret-key-do-not-share",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"

    # Local development and tests fall back to SQLite when DATABASE_URL is unset.
    database_url: str = "sqlite:///./inkloom_dev.db"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 30.0

    cors_origins: str = "http://localhost:5173,https://inkloom-ai-wheat.vercel.app"

    # In production, jwt_secret_key must be explicitly set to a unique, strong value (>= 32 chars).
    # In development/test, an empty value automatically falls back to a safe random per-process secret.
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # DEMO_SEED_PASSWORD must be explicitly provided in environment when seeding demo accounts.
    # No fallback demo password is hardcoded to prevent unintentional production exposure.
    demo_seed_password: str = ""

    max_content_chars: int = 10_000
    analyze_rate_limit_per_minute: int = 10

    @property
    def is_production(self) -> bool:
        env = self.environment.lower().strip()
        if env in ("production", "prod"):
            return True
        if env in ("test", "testing", "development", "dev", "local"):
            return False
        # If database points to external PostgreSQL and not marked dev/test
        return not self.database_url.startswith("sqlite")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        key = (self.jwt_secret_key or "").strip()
        if self.is_production:
            if not key:
                raise ValueError(
                    "JWT_SECRET_KEY is required in production. "
                    "Generate a strong secret with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            if key in KNOWN_INSECURE_JWT_SECRETS:
                raise ValueError(
                    "Known insecure development JWT_SECRET_KEY detected in production. "
                    "Production requires an independently generated random secret."
                )
            if len(key) < 32:
                raise ValueError(
                    f"JWT_SECRET_KEY must be at least 32 characters long in production (current length: {len(key)})."
                )
        else:
            # Local development fallback: use per-process random secret if none was provided
            if not key:
                object.__setattr__(self, "jwt_secret_key", _DEV_RANDOM_SECRET)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
