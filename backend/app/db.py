"""Database engine, session factory and declarative base.

Centrally controlled contract file.

Supabase note: on Render, use the Supavisor session pooler URL (port 5432).
If the transaction pooler (port 6543) is used instead, psycopg prepared
statements must be disabled, which is handled below.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalise_url(url: str) -> str:
    # Supabase and Render hand out postgres:// or postgresql:// URLs.
    # SQLAlchemy needs the psycopg 3 driver named explicitly.
    if url.startswith("postgres://"):
        url = "postgresql://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def build_engine(url: str) -> Engine:
    url = _normalise_url(url)
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    connect_args: dict[str, object] = {}
    if ":6543/" in url:
        connect_args["prepare_threshold"] = None
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, connect_args=connect_args)


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind: Engine | None = None) -> None:
    """Create all tables (MVP strategy: create_all, no Alembic)."""
    from app import models  # noqa: F401  (register models on Base.metadata)

    Base.metadata.create_all(bind=bind or engine)
