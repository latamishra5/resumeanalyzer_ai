"""Unified SQLAlchemy database engine, schema metadata, and dialect helpers (SQLite + PostgreSQL)."""

import importlib.util
import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    inspect,
    text,
)
from sqlalchemy.pool import NullPool

from backend.config.settings import ENV_PATH, FEEDBACK_DB_PATH, RESUME_DB_PATH

METADATA = MetaData()

resume_data_table = Table(
    "resume_data",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("name", Text, nullable=False),
    Column("email", Text, nullable=False),
    Column("phone", Text, nullable=False),
    Column("linkedin", Text),
    Column("github", Text),
    Column("portfolio", Text),
    Column("summary", Text),
    Column("target_role", Text),
    Column("target_category", Text),
    Column("education", Text),
    Column("experience", Text),
    Column("projects", Text),
    Column("skills", Text),
    Column("template", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

resume_skills_table = Table(
    "resume_skills",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("resume_id", Integer, ForeignKey("resume_data.id")),
    Column("skill_name", Text, nullable=False),
    Column("skill_category", Text, nullable=False),
    Column("proficiency_score", Float),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

resume_analysis_table = Table(
    "resume_analysis",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("resume_id", Integer, ForeignKey("resume_data.id")),
    Column("ats_score", Float),
    Column("keyword_match_score", Float),
    Column("format_score", Float),
    Column("section_score", Float),
    Column("missing_skills", Text),
    Column("recommendations", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

ai_analysis_table = Table(
    "ai_analysis",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("resume_id", Integer, ForeignKey("resume_data.id")),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=True),
    Column("model_used", Text),
    Column("resume_score", Integer),
    Column("job_role", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

admin_table = Table(
    "admin",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password", Text, nullable=False),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

admin_logs_table = Table(
    "admin_logs",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("admin_email", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("timestamp", DateTime, server_default=func.current_timestamp()),
)

users_table = Table(
    "users",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(120), nullable=False, unique=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", Text, nullable=False),
    Column("full_name", Text),
    Column("phone", Text),
    Column("linkedin", Text),
    Column("github", Text),
    Column("portfolio", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
    Column("last_login", DateTime),
    Column("is_active", Integer, default=1, server_default=text("1")),
)

user_sessions_table = Table(
    "user_sessions",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("session_token", String(255), nullable=False, unique=True),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
    Column("expires_at", DateTime, nullable=False),
    Column("ip_address", Text),
    Column("user_agent", Text),
)

user_activity_table = Table(
    "user_activity",
    METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("activity_type", Text, nullable=False),
    Column("activity_details", Text),
    Column("ip_address", Text),
    Column("created_at", DateTime, server_default=func.current_timestamp()),
)

FEEDBACK_METADATA = MetaData()

feedback_table = Table(
    "feedback",
    FEEDBACK_METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rating", Integer),
    Column("usability_score", Integer),
    Column("feature_satisfaction", Integer),
    Column("missing_features", Text),
    Column("improvement_suggestions", Text),
    Column("user_experience", Text),
    Column("timestamp", DateTime, server_default=func.current_timestamp()),
)

_PG_ENGINE_LOCK = Lock()
_PG_ENGINES = {}


def normalize_database_url(raw_url: str | None) -> str | None:
    """Normalize PostgreSQL and SQLite connection URLs for SQLAlchemy."""
    if not raw_url:
        return None
    cleaned = raw_url.strip()
    if not cleaned:
        return None

    if cleaned.startswith("postgres://"):
        cleaned = "postgresql://" + cleaned[len("postgres://"):]

    if cleaned.startswith("postgresql://"):
        # Prefer pure-python pg8000 if psycopg2 is unavailable
        if importlib.util.find_spec("psycopg2") is None and importlib.util.find_spec("pg8000") is not None:
            cleaned = "postgresql+pg8000://" + cleaned[len("postgresql://"):]

    return cleaned


def resolve_database_url(db_url: str | None = None, db_path: Path | str | None = None, role: str = "main") -> str:
    """Resolve explicit db_path, explicit db_url, env DATABASE_URL, or default SQLite path."""
    if db_path is not None:
        resolved = Path(db_path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{resolved}"

    if db_url:
        normalized = normalize_database_url(db_url)
        if normalized:
            return normalized

    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=False)
    env_url = normalize_database_url(os.getenv("DATABASE_URL"))
    if env_url:
        return env_url

    default_path = Path(FEEDBACK_DB_PATH if role == "feedback" else RESUME_DB_PATH)
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{default_path}"


def is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql")


def get_engine(db_url: str | None = None, db_path: Path | str | None = None, role: str = "main"):
    """Return a SQLAlchemy Engine. SQLite uses NullPool so file locks release immediately."""
    resolved_url = resolve_database_url(db_url=db_url, db_path=db_path, role=role)
    if resolved_url.startswith("sqlite:"):
        return create_engine(
            resolved_url,
            poolclass=NullPool,
            connect_args={"check_same_thread": False},
        )

    with _PG_ENGINE_LOCK:
        engine = _PG_ENGINES.get(resolved_url)
        if engine is None:
            engine = create_engine(
                resolved_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
            _PG_ENGINES[resolved_url] = engine
        return engine


def _ensure_column(engine, table_name: str, column_name: str, ddl_type: str) -> None:
    """Idempotently add a nullable column when upgrading an existing database schema."""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return
    existing = {col["name"] for col in inspector.get_columns(table_name)}
    if column_name in existing:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"))


def init_all_tables(engine, include_feedback: bool = True):
    """Create schema tables idempotently for SQLite or PostgreSQL."""
    METADATA.create_all(engine)
    _ensure_column(engine, "resume_data", "user_id", "INTEGER")
    _ensure_column(engine, "ai_analysis", "user_id", "INTEGER")
    if include_feedback:
        FEEDBACK_METADATA.create_all(engine)


def table_exists(engine, table_name: str) -> bool:
    """Return True if a table exists in the given engine."""
    return inspect(engine).has_table(table_name)


def get_storage_size_label(engine, sqlite_path: Path | None = None) -> str:
    """Return human-readable storage size for SQLite file or PostgreSQL database."""
    url_str = str(engine.url)
    if url_str.startswith("sqlite:"):
        if sqlite_path is None and engine.url.database:
            sqlite_path = Path(engine.url.database)
        if not sqlite_path or not sqlite_path.exists():
            return "0 B"
        size_bytes = sqlite_path.stat().st_size
    elif is_postgres_url(url_str):
        with engine.connect() as conn:
            size_bytes = conn.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0
    else:
        return "N/A"

    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"
