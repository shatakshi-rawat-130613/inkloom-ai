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
    """Run versioned Alembic migrations to ensure schema is at head.
    
    If the database already contains tables but no alembic_version table,
    it stamps revision 001_initial_schema before upgrading to head.
    """
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    target_engine = bind or engine

    from app import models  # noqa: F401  (register models on Base.metadata)

    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(target_engine.url))

    inspector = inspect(target_engine)
    existing_tables = set(inspector.get_table_names())

    with target_engine.begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        if "organisations" in existing_tables and "alembic_version" not in existing_tables:
            command.stamp(alembic_cfg, "001_initial_schema")
        command.upgrade(alembic_cfg, "head")
