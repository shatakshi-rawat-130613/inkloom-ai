"""Application settings loaded from environment variables.

Centrally controlled contract file. See .env.example for documentation.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Local development and tests fall back to SQLite when DATABASE_URL is unset.
    database_url: str = "sqlite:///./inkloom_dev.db"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 30.0

    cors_origins: str = "http://localhost:5173,https://inkloom-ai-wheat.vercel.app"

    jwt_secret_key: str = "inkloom-production-jwt-secret-key-do-not-share-32charsmin"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # DEMO_SEED_PASSWORD must be explicitly provided in environment.
    # No fallback demo password is hardcoded to prevent unintentional production exposure.
    demo_seed_password: str = ""

    max_content_chars: int = 10_000
    analyze_rate_limit_per_minute: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def ai_enabled(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
