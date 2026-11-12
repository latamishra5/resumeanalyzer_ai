"""Database connection and query helpers (SQLite locally or PostgreSQL via DATABASE_URL)."""

import logging
from pathlib import Path

from sqlalchemy import func, select, text

from backend.config.settings import ENV_PATH, RESUME_DB_PATH
from backend.database.db import (
    ai_analysis_table,
    get_engine,
    init_all_tables,
    resume_analysis_table,
    resume_data_table,
    table_exists,
)

logger = logging.getLogger(__name__)
_DEFAULT_RESUME_DB_PATH = Path(RESUME_DB_PATH)


def _active_engine():
    """Return engine for configured DATABASE_URL or patched RESUME_DB_PATH."""
    if Path(RESUME_DB_PATH) != _DEFAULT_RESUME_DB_PATH:
        return get_engine(db_path=RESUME_DB_PATH)
    return get_engine(role="main")


def _get_admin_service():
    from backend.admin.service import AdminService

    if Path(RESUME_DB_PATH) != _DEFAULT_RESUME_DB_PATH:
        return AdminService(resume_db_path=RESUME_DB_PATH, env_path=ENV_PATH)
    return AdminService(env_path=ENV_PATH)


def get_database_connection(check_same_thread: bool = True):
    """Create and return a raw DBAPI connection (used by legacy callers)."""
    return _active_engine().raw_connection()


def init_database():
    """Initialize all core database tables cleanly for SQLite or PostgreSQL."""
    engine = _active_engine()
    init_all_tables(engine, include_feedback=(engine.dialect.name != "sqlite"))


def _coerce_user_id(user_id) -> int | None:
    """Return integer user ID when authenticated, or None for guest sessions."""
    if isinstance(user_id, bool) or user_id is None:
        return None
    if isinstance(user_id, int):
        return user_id if user_id > 0 else None
    try:
        parsed = int(str(user_id).strip())
        return parsed if parsed > 0 else None
    except (TypeError, ValueError):
        return None


def save_resume_data(data, user_id=None):
    """Save resume data to database and return the created resume ID."""
    engine = _active_engine()
    resolved_user_id = _coerce_user_id(user_id if user_id is not None else data.get("user_id"))
    try:
        personal_info = data.get("personal_info", {})
        full_name = personal_info.get("full_name") or personal_info.get("name", "")
        with engine.begin() as conn:
            res = conn.execute(
                resume_data_table.insert().values(
                    user_id=resolved_user_id,
                    name=full_name,
                    email=personal_info.get("email", ""),
                    phone=personal_info.get("phone", ""),
                    linkedin=personal_info.get("linkedin", ""),
                    github=personal_info.get("github", ""),
                    portfolio=personal_info.get("portfolio", ""),
                    summary=data.get("summary", ""),
                    target_role=data.get("target_role", ""),
                    target_category=data.get("target_category", ""),
                    education=str(data.get("education", [])),
                    experience=str(data.get("experience", [])),
                    projects=str(data.get("projects", [])),
                    skills=str(data.get("skills", [])),
                    template=data.get("template", ""),
                )
            )
            return res.inserted_primary_key[0]
    except Exception as exc:
        logger.exception("Error saving resume data: %s", exc)
        return None


def save_analysis_data(resume_id, analysis):
    """Save resume analysis data."""
    engine = _active_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                resume_analysis_table.insert().values(
                    resume_id=resume_id,
                    ats_score=float(analysis.get("ats_score", 0)),
                    keyword_match_score=float(analysis.get("keyword_match_score", 0)),
                    format_score=float(analysis.get("format_score", 0)),
                    section_score=float(analysis.get("section_score", 0)),
                    missing_skills=analysis.get("missing_skills", ""),
                    recommendations=analysis.get("recommendations", ""),
                )
            )
    except Exception as exc:
        logger.exception("Error saving analysis data: %s", exc)


def get_resume_stats():
    """Get summary statistics about resumes."""
    engine = _active_engine()
    try:
        with engine.connect() as conn:
            total_resumes = conn.execute(select(func.count()).select_from(resume_data_table)).scalar() or 0
            avg_ats_score = conn.execute(select(func.avg(resume_analysis_table.c.ats_score))).scalar() or 0
            recent_rows = conn.execute(
                select(
                    resume_data_table.c.name,
                    resume_data_table.c.target_role,
                    resume_data_table.c.created_at,
                )
                .order_by(resume_data_table.c.created_at.desc())
                .limit(5)
            ).fetchall()
            return {
                "total_resumes": total_resumes,
                "avg_ats_score": round(float(avg_ats_score), 2),
                "recent_activity": [tuple(row) for row in recent_rows],
            }
    except Exception as exc:
        logger.exception("Error getting resume stats: %s", exc)
        return None


def log_admin_action(admin_email, action):
    """Log admin actions via the backend admin service."""
    _get_admin_service().log_admin_action(admin_email, action)


def get_admin_logs():
    """Get admin activity logs via the backend admin service."""
    return _get_admin_service().get_admin_logs()


def get_all_resume_data():
    """Get all resume data joined with analysis scores."""
    engine = _active_engine()
    try:
        stmt = text("""
            SELECT
                r.id, r.name, r.email, r.phone, r.linkedin, r.github, r.portfolio,
                r.target_role, r.target_category, r.created_at,
                a.ats_score, a.keyword_match_score, a.format_score, a.section_score
            FROM resume_data r
            LEFT JOIN resume_analysis a ON r.id = a.resume_id
            ORDER BY r.created_at DESC
        """)
        with engine.connect() as conn:
            return [tuple(row) for row in conn.execute(stmt).fetchall()]
    except Exception as exc:
        logger.exception("Error getting resume data: %s", exc)
        return []


def verify_admin(email, password):
    """Verify admin credentials via the backend admin service."""
    try:
        return _get_admin_service().verify_admin(email, password)
    except Exception as exc:
        logger.exception("Error verifying admin: %s", exc)
        return False


def add_admin(email, password):
    """Add a new admin with a salted scrypt password hash via the backend admin service."""
    try:
        ok, _ = _get_admin_service().add_admin(email, password)
        return ok
    except Exception as exc:
        logger.exception("Error adding admin: %s", exc)
        return False


def get_user_resumes_history(user_id, limit: int = 25):
    """Get resume and analysis history scoped to a specific authenticated user."""
    resolved_user_id = _coerce_user_id(user_id)
    if resolved_user_id is None:
        return []
    engine = _active_engine()
    try:
        stmt = text("""
            SELECT
                r.id, r.name, r.target_role, r.target_category, r.template, r.created_at,
                a.ats_score, a.keyword_match_score, a.format_score, a.section_score
            FROM resume_data r
            LEFT JOIN resume_analysis a ON r.id = a.resume_id
            WHERE r.user_id = :uid
            ORDER BY r.created_at DESC, r.id DESC
            LIMIT :limit
        """)
        with engine.connect() as conn:
            rows = conn.execute(stmt, {"uid": resolved_user_id, "limit": limit}).fetchall()
        return [
            {
                "id": r[0],
                "name": r[1],
                "target_role": r[2],
                "target_category": r[3],
                "template": r[4],
                "created_at": str(r[5] or ""),
                "ats_score": float(r[6]) if r[6] is not None else None,
                "keyword_match_score": float(r[7]) if r[7] is not None else None,
                "format_score": float(r[8]) if r[8] is not None else None,
                "section_score": float(r[9]) if r[9] is not None else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.exception("Error fetching user resume history: %s", exc)
        return []


def save_ai_analysis_data(resume_id, analysis_data, user_id=None):
    """Save AI analysis data to the database."""
    engine = _active_engine()
    resolved_user_id = _coerce_user_id(user_id if user_id is not None else analysis_data.get("user_id"))
    try:
        if not table_exists(engine, "ai_analysis"):
            init_all_tables(engine, include_feedback=False)
        with engine.begin() as conn:
            res = conn.execute(
                ai_analysis_table.insert().values(
                    resume_id=resume_id,
                    user_id=resolved_user_id,
                    model_used=analysis_data.get("model_used", ""),
                    resume_score=analysis_data.get("resume_score", 0),
                    job_role=analysis_data.get("job_role", ""),
                )
            )
            return res.inserted_primary_key[0]
    except Exception as exc:
        logger.exception("Error saving AI analysis data: %s", exc)
        raise


def get_ai_analysis_stats(user_id=None):
    """Get statistics about AI analyzer usage (optionally scoped to user_id)."""
    engine = _active_engine()
    resolved_user_id = _coerce_user_id(user_id)
    empty = {
        "total_analyses": 0,
        "model_usage": [],
        "average_score": 0,
        "top_job_roles": [],
    }
    try:
        if not table_exists(engine, "ai_analysis"):
            return empty
        with engine.connect() as conn:
            total_stmt = select(func.count()).select_from(ai_analysis_table)
            model_stmt = select(ai_analysis_table.c.model_used, func.count().label("c"))
            avg_stmt = select(func.avg(ai_analysis_table.c.resume_score))
            role_stmt = select(ai_analysis_table.c.job_role, func.count().label("c"))
            if resolved_user_id is not None:
                cond = ai_analysis_table.c.user_id == resolved_user_id
                total_stmt = total_stmt.where(cond)
                model_stmt = model_stmt.where(cond)
                avg_stmt = avg_stmt.where(cond)
                role_stmt = role_stmt.where(cond)

            total = conn.execute(total_stmt).scalar() or 0
            model_rows = conn.execute(
                model_stmt.group_by(ai_analysis_table.c.model_used).order_by(text("c DESC"))
            ).fetchall()
            avg_score = conn.execute(avg_stmt).scalar() or 0
            role_rows = conn.execute(
                role_stmt.group_by(ai_analysis_table.c.job_role).order_by(text("c DESC")).limit(5)
            ).fetchall()
            return {
                "total_analyses": total,
                "model_usage": [{"model": r[0], "count": r[1]} for r in model_rows],
                "average_score": round(float(avg_score), 1),
                "top_job_roles": [{"role": r[0], "count": r[1]} for r in role_rows],
            }
    except Exception as exc:
        logger.exception("Error getting AI analysis stats: %s", exc)
        return empty


def get_detailed_ai_analysis_stats():
    """Get detailed statistics about AI analyzer usage including daily trends."""
    return _get_admin_service().get_detailed_ai_stats()


def reset_ai_analysis_stats():
    """Reset AI analysis statistics via the backend admin service."""
    try:
        ok, message = _get_admin_service().reset_ai_stats(actor_email="system")
        return {"success": ok, "message": message}
    except Exception as exc:
        logger.exception("Error resetting AI analysis stats: %s", exc)
        return {"success": False, "message": f"Error resetting AI analysis statistics: {str(exc)}"}
