"""Backend Admin Service: authentication, audit logs, resume/AI/feedback/user management (SQLite + PostgreSQL)."""

from collections import Counter
from datetime import datetime, timedelta, timezone
import hmac
from io import BytesIO
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import text

from backend.auth.security import hash_password, verify_password
from backend.config.settings import ENV_PATH
from backend.database.db import (
    admin_logs_table,
    admin_table,
    get_engine,
    get_storage_size_label,
    init_all_tables,
    table_exists,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ts_param(engine, dt: datetime):
    if engine.dialect.name == "sqlite":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


class AdminService:
    """UI-agnostic administrative service backed by SQLite locally or PostgreSQL via DATABASE_URL."""

    def __init__(self, resume_db_path=None, feedback_db_path=None, env_path=None, database_url=None):
        self.resume_db_path = Path(resume_db_path) if resume_db_path else None
        self.feedback_db_path = Path(feedback_db_path) if feedback_db_path else None
        self.env_path = Path(env_path) if env_path else Path(ENV_PATH)
        self.database_url = database_url

        self.main_engine = get_engine(db_url=database_url, db_path=self.resume_db_path, role="main")
        self.feedback_engine = get_engine(db_url=database_url, db_path=self.feedback_db_path, role="feedback")
        self.ensure_admin_tables()

    def ensure_admin_tables(self):
        """Ensure core resume, analysis, and admin tables exist."""
        init_all_tables(self.main_engine, include_feedback=(self.main_engine.dialect.name != "sqlite"))

    def _load_env_admin(self) -> tuple[str, str]:
        if self.env_path.exists():
            load_dotenv(self.env_path, override=False)
        env_email = os.getenv("ADMIN_EMAIL", "").strip()
        env_password = os.getenv("ADMIN_PASSWORD", "")
        return env_email, env_password

    def has_env_admin(self) -> bool:
        env_email, env_password = self._load_env_admin()
        return bool(env_email and env_password)

    def has_any_admin(self) -> bool:
        """Return True when at least one env or database admin credential is configured."""
        if self.has_env_admin():
            return True
        with self.main_engine.connect() as conn:
            row = conn.execute(text("SELECT 1 FROM admin LIMIT 1")).fetchone()
            return row is not None

    def verify_admin(self, email: str, password: str) -> bool:
        """Verify admin credentials against environment config or hashed database records."""
        if not email or not password:
            return False

        normalized_email = email.strip()
        env_email, env_password = self._load_env_admin()
        if (
            env_email
            and env_password
            and hmac.compare_digest(normalized_email.lower(), env_email.lower())
            and hmac.compare_digest(password, env_password)
        ):
            return True

        with self.main_engine.begin() as conn:
            row = conn.execute(
                text("SELECT id, password FROM admin WHERE lower(email) = lower(:em)"),
                {"em": normalized_email},
            ).fetchone()
            if not row:
                return False

            admin_id, stored_password = row
            is_valid, needs_rehash = verify_password(password, stored_password)
            if is_valid and needs_rehash:
                conn.execute(
                    text("UPDATE admin SET password = :pw WHERE id = :aid"),
                    {"pw": hash_password(password), "aid": admin_id},
                )
            return is_valid

    def add_admin(self, email: str, password: str, actor_email: str | None = None) -> tuple[bool, str]:
        """Add a new admin account with a salted scrypt password hash."""
        normalized_email = (email or "").strip()
        if not normalized_email or "@" not in normalized_email:
            return False, "Please enter a valid admin email address."
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."

        with self.main_engine.begin() as conn:
            existing = conn.execute(
                text("SELECT 1 FROM admin WHERE lower(email) = lower(:em)"),
                {"em": normalized_email},
            ).fetchone()
            if existing:
                return False, f"Admin account already exists for {normalized_email}."

            conn.execute(
                admin_table.insert().values(email=normalized_email, password=hash_password(password))
            )

        if actor_email:
            self.log_admin_action(actor_email, f"Added admin account: {normalized_email}")
        return True, f"Admin account created for {normalized_email}."

    def update_admin_password(
        self,
        email: str,
        new_password: str,
        actor_email: str | None = None,
    ) -> tuple[bool, str]:
        """Reset or update the password hash for an existing admin account."""
        normalized_email = (email or "").strip()
        if not normalized_email:
            return False, "Admin email is required."
        if not new_password or len(new_password) < 8:
            return False, "New password must be at least 8 characters long."

        with self.main_engine.begin() as conn:
            res = conn.execute(
                text("UPDATE admin SET password = :pw WHERE lower(email) = lower(:em)"),
                {"pw": hash_password(new_password), "em": normalized_email},
            )
            if res.rowcount == 0:
                return False, f"No database admin found for {normalized_email}."

        self.log_admin_action(actor_email or normalized_email, f"Updated password for: {normalized_email}")
        return True, f"Password updated for {normalized_email}."

    def replace_with_single_admin(self, email: str, password: str) -> tuple[bool, str]:
        """Replace all existing DB admins with a single newly created hashed admin account."""
        normalized_email = (email or "").strip()
        if not normalized_email or "@" not in normalized_email:
            return False, "Please enter a valid admin email address."
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."

        with self.main_engine.begin() as conn:
            conn.execute(text("DELETE FROM admin"))
            conn.execute(
                admin_table.insert().values(email=normalized_email, password=hash_password(password))
            )
        return True, f"Admin account reset for {normalized_email}."

    def delete_admin(self, email: str, actor_email: str | None = None) -> tuple[bool, str]:
        """Delete a database admin account while preventing self-lockout."""
        normalized_email = (email or "").strip()
        if not normalized_email:
            return False, "Admin email is required."
        if actor_email and normalized_email.lower() == actor_email.strip().lower():
            return False, "You cannot delete the currently signed-in admin account."

        with self.main_engine.begin() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM admin")).scalar() or 0
            if total <= 1 and not self.has_env_admin():
                return False, "Cannot delete the last remaining admin account."
            res = conn.execute(
                text("DELETE FROM admin WHERE lower(email) = lower(:em)"),
                {"em": normalized_email},
            )
            if res.rowcount == 0:
                return False, f"Admin account not found: {normalized_email}"

        if actor_email:
            self.log_admin_action(actor_email, f"Deleted admin account: {normalized_email}")
        return True, f"Deleted admin account: {normalized_email}"

    def list_admins(self) -> list[dict]:
        """List registered database admin accounts without exposing password hashes."""
        with self.main_engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, email, created_at FROM admin ORDER BY created_at DESC, id DESC")
            ).fetchall()
        return [{"id": r[0], "email": r[1], "created_at": r[2]} for r in rows]

    def log_admin_action(self, admin_email: str, action: str) -> None:
        """Record an admin audit log entry."""
        if not admin_email or not action:
            return
        with self.main_engine.begin() as conn:
            conn.execute(
                admin_logs_table.insert().values(admin_email=admin_email.strip(), action=action)
            )

    def get_admin_logs(self, limit: int | None = None) -> list[tuple[str, str, str]]:
        """Fetch admin audit logs sorted newest first."""
        stmt = "SELECT admin_email, action, timestamp FROM admin_logs ORDER BY timestamp DESC, id DESC"
        params = {}
        if limit is not None:
            stmt += " LIMIT :lim"
            params["lim"] = int(limit)

        with self.main_engine.connect() as conn:
            return [tuple(r) for r in conn.execute(text(stmt), params).fetchall()]

    def get_admin_logs_dataframe(self, limit: int | None = None) -> pd.DataFrame:
        logs = self.get_admin_logs(limit=limit)
        if not logs:
            return pd.DataFrame(columns=["Admin Email", "Action", "Timestamp"])
        return pd.DataFrame(logs, columns=["Admin Email", "Action", "Timestamp"])

    def clear_admin_logs(self, actor_email: str) -> tuple[bool, str]:
        """Clear historical admin logs and record the reset action."""
        with self.main_engine.begin() as conn:
            conn.execute(text("DELETE FROM admin_logs"))
            conn.execute(
                admin_logs_table.insert().values(
                    admin_email=actor_email.strip(),
                    action="Cleared admin audit logs",
                )
            )
        return True, "Admin audit logs cleared."

    def get_system_overview(self) -> dict:
        """Aggregate cross-table system health, volume, and database size stats."""
        now_utc = _utc_now()
        start_of_day = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

        overview = {
            "total_resumes": 0,
            "today_submissions": 0,
            "total_analyses": 0,
            "avg_ats_score": 0.0,
            "ai_total_analyses": 0,
            "ai_avg_score": 0.0,
            "total_users": 0,
            "admin_count": 0,
            "total_feedback": 0,
            "avg_feedback_rating": 0.0,
            "resume_db_size": get_storage_size_label(self.main_engine, self.resume_db_path),
            "feedback_db_size": get_storage_size_label(self.feedback_engine, self.feedback_db_path),
        }

        with self.main_engine.connect() as conn:
            overview["total_resumes"] = conn.execute(text("SELECT COUNT(*) FROM resume_data")).scalar() or 0
            overview["today_submissions"] = conn.execute(
                text("SELECT COUNT(*) FROM resume_data WHERE created_at >= :start_dt"),
                {"start_dt": _ts_param(self.main_engine, start_of_day)},
            ).scalar() or 0
            overview["total_analyses"] = conn.execute(text("SELECT COUNT(*) FROM resume_analysis")).scalar() or 0
            avg_ats = conn.execute(text("SELECT AVG(ats_score) FROM resume_analysis")).scalar()
            overview["avg_ats_score"] = round(float(avg_ats or 0), 1)
            overview["admin_count"] = conn.execute(text("SELECT COUNT(*) FROM admin")).scalar() or 0

            if table_exists(self.main_engine, "ai_analysis"):
                overview["ai_total_analyses"] = conn.execute(text("SELECT COUNT(*) FROM ai_analysis")).scalar() or 0
                ai_avg = conn.execute(text("SELECT AVG(resume_score) FROM ai_analysis")).scalar()
                overview["ai_avg_score"] = round(float(ai_avg or 0), 1)

            if table_exists(self.main_engine, "users"):
                overview["total_users"] = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0

        if table_exists(self.feedback_engine, "feedback"):
            with self.feedback_engine.connect() as fconn:
                row = fconn.execute(text("SELECT COUNT(*), AVG(rating) FROM feedback")).fetchone()
                overview["total_feedback"] = int((row[0] if row else 0) or 0)
                overview["avg_feedback_rating"] = round(float((row[1] if row else 0) or 0), 2)

        return overview

    def get_all_resumes_dataframe(self) -> pd.DataFrame:
        """Return joined resume submissions and latest analysis metrics as a DataFrame."""
        stmt = text("""
            SELECT
                rd.id AS "ID",
                rd.name AS "Name",
                rd.email AS "Email",
                rd.phone AS "Phone",
                rd.linkedin AS "LinkedIn",
                rd.github AS "GitHub",
                rd.portfolio AS "Portfolio",
                rd.target_role AS "Target Role",
                rd.target_category AS "Target Category",
                rd.summary AS "Summary",
                rd.skills AS "Skills",
                rd.experience AS "Experience",
                rd.education AS "Education",
                rd.projects AS "Projects",
                rd.template AS "Template",
                rd.created_at AS "Submission Date",
                ra.ats_score AS "ATS Score",
                ra.keyword_match_score AS "Keyword Match",
                ra.format_score AS "Format Score",
                ra.section_score AS "Section Score",
                ra.missing_skills AS "Missing Skills",
                ra.recommendations AS "Recommendations"
            FROM resume_data rd
            LEFT JOIN resume_analysis ra
                ON ra.id = (
                    SELECT ra2.id
                    FROM resume_analysis ra2
                    WHERE ra2.resume_id = rd.id
                    ORDER BY ra2.created_at DESC, ra2.id DESC
                    LIMIT 1
                )
            ORDER BY rd.created_at DESC, rd.id DESC
        """)
        with self.main_engine.connect() as conn:
            return pd.read_sql_query(stmt, conn)

    def delete_resume_record(self, resume_id: int, actor_email: str) -> tuple[bool, str]:
        """Delete a resume submission and its linked analysis/skill rows."""
        rid = int(resume_id)
        with self.main_engine.begin() as conn:
            row = conn.execute(
                text("SELECT name, email FROM resume_data WHERE id = :rid"),
                {"rid": rid},
            ).fetchone()
            if not row:
                return False, f"Resume ID {resume_id} not found."

            conn.execute(text("DELETE FROM resume_analysis WHERE resume_id = :rid"), {"rid": rid})
            conn.execute(text("DELETE FROM resume_skills WHERE resume_id = :rid"), {"rid": rid})
            if table_exists(self.main_engine, "ai_analysis"):
                conn.execute(text("DELETE FROM ai_analysis WHERE resume_id = :rid"), {"rid": rid})
            conn.execute(text("DELETE FROM resume_data WHERE id = :rid"), {"rid": rid})

        self.log_admin_action(actor_email, f"Deleted resume #{resume_id} ({row[0]} / {row[1]})")
        return True, f"Deleted resume record #{resume_id}."

    def get_detailed_ai_stats(self) -> dict:
        """Return detailed AI analyzer usage statistics cleanly across SQLite & PostgreSQL."""
        empty = {
            "total_analyses": 0,
            "model_usage": [],
            "average_score": 0,
            "top_job_roles": [],
            "daily_trend": [],
            "score_distribution": [],
            "recent_analyses": [],
        }
        if not table_exists(self.main_engine, "ai_analysis"):
            return empty

        cutoff_dt = _utc_now() - timedelta(days=30)
        with self.main_engine.connect() as conn:
            total_analyses = conn.execute(text("SELECT COUNT(*) FROM ai_analysis")).scalar() or 0
            if total_analyses == 0:
                return empty

            model_usage = [
                {"model": r[0], "count": r[1]}
                for r in conn.execute(
                    text("SELECT model_used, COUNT(*) AS c FROM ai_analysis GROUP BY model_used ORDER BY c DESC")
                ).fetchall()
            ]
            avg_score = conn.execute(text("SELECT AVG(resume_score) FROM ai_analysis")).scalar() or 0
            top_job_roles = [
                {"role": r[0], "count": r[1]}
                for r in conn.execute(
                    text("SELECT job_role, COUNT(*) AS c FROM ai_analysis GROUP BY job_role ORDER BY c DESC LIMIT 8")
                ).fetchall()
            ]
            trend_rows = conn.execute(
                text("SELECT created_at FROM ai_analysis WHERE created_at >= :cutoff ORDER BY created_at ASC"),
                {"cutoff": _ts_param(self.main_engine, cutoff_dt)},
            ).fetchall()
            day_counter = Counter(str(r[0])[:10] for r in trend_rows if r[0])
            daily_trend = [{"date": d, "count": day_counter[d]} for d in sorted(day_counter)]

            score_distribution = []
            for low, high, label in (
                (0, 20, "0-20"),
                (21, 40, "21-40"),
                (41, 60, "41-60"),
                (61, 80, "61-80"),
                (81, 100, "81-100"),
            ):
                count = conn.execute(
                    text("SELECT COUNT(*) FROM ai_analysis WHERE resume_score >= :lo AND resume_score <= :hi"),
                    {"lo": low, "hi": high},
                ).scalar() or 0
                score_distribution.append({"range": label, "count": int(count)})

            recent_analyses = [
                {
                    "model": r[0],
                    "score": r[1],
                    "job_role": r[2],
                    "date": str(r[3])[:19] if r[3] else "",
                }
                for r in conn.execute(
                    text("SELECT model_used, resume_score, job_role, created_at FROM ai_analysis ORDER BY created_at DESC LIMIT 20")
                ).fetchall()
            ]

            return {
                "total_analyses": int(total_analyses),
                "model_usage": model_usage,
                "average_score": round(float(avg_score), 1),
                "top_job_roles": top_job_roles,
                "daily_trend": daily_trend,
                "score_distribution": score_distribution,
                "recent_analyses": recent_analyses,
            }

    def reset_ai_stats(self, actor_email: str) -> tuple[bool, str]:
        """Truncate ai_analysis records and audit-log the reset."""
        if not table_exists(self.main_engine, "ai_analysis"):
            return False, "No AI analysis table exists yet."
        with self.main_engine.begin() as conn:
            conn.execute(text("DELETE FROM ai_analysis"))
        self.log_admin_action(actor_email, "Reset AI analysis statistics")
        return True, "AI analysis statistics have been reset."

    def get_feedback_dataframe(self) -> pd.DataFrame:
        """Return all submitted user feedback rows."""
        columns = [
            "ID", "Rating", "Usability Score", "Feature Satisfaction",
            "Missing Features", "Improvement Suggestions", "User Experience", "Timestamp",
        ]
        if not table_exists(self.feedback_engine, "feedback"):
            return pd.DataFrame(columns=columns)

        stmt = text("""
            SELECT
                id AS "ID",
                rating AS "Rating",
                usability_score AS "Usability Score",
                feature_satisfaction AS "Feature Satisfaction",
                missing_features AS "Missing Features",
                improvement_suggestions AS "Improvement Suggestions",
                user_experience AS "User Experience",
                timestamp AS "Timestamp"
            FROM feedback
            ORDER BY timestamp DESC, id DESC
        """)
        with self.feedback_engine.connect() as fconn:
            return pd.read_sql_query(stmt, fconn)

    def delete_feedback_entry(self, feedback_id: int, actor_email: str) -> tuple[bool, str]:
        """Delete a feedback row by ID and log the action."""
        if not table_exists(self.feedback_engine, "feedback"):
            return False, "Feedback table does not exist."
        with self.feedback_engine.begin() as fconn:
            res = fconn.execute(
                text("DELETE FROM feedback WHERE id = :fid"),
                {"fid": int(feedback_id)},
            )
            if res.rowcount == 0:
                return False, f"Feedback ID {feedback_id} not found."
        self.log_admin_action(actor_email, f"Deleted feedback #{feedback_id}")
        return True, f"Deleted feedback entry #{feedback_id}."

    def get_users_dataframe(self) -> pd.DataFrame:
        """Return registered application users (excluding password hashes)."""
        columns = ["ID", "Username", "Email", "Full Name", "Phone", "Active", "Created At", "Last Login"]
        if not table_exists(self.main_engine, "users"):
            return pd.DataFrame(columns=columns)
        stmt = text("""
            SELECT
                id AS "ID",
                username AS "Username",
                email AS "Email",
                full_name AS "Full Name",
                phone AS "Phone",
                is_active AS "Active",
                created_at AS "Created At",
                last_login AS "Last Login"
            FROM users
            ORDER BY created_at DESC, id DESC
        """)
        with self.main_engine.connect() as conn:
            return pd.read_sql_query(stmt, conn)

    def set_user_active(self, user_id: int, is_active: bool, actor_email: str) -> tuple[bool, str]:
        """Enable or disable a registered user account."""
        if not table_exists(self.main_engine, "users"):
            return False, "Users table does not exist."
        with self.main_engine.begin() as conn:
            res = conn.execute(
                text("UPDATE users SET is_active = :active WHERE id = :uid"),
                {"active": 1 if is_active else 0, "uid": int(user_id)},
            )
            if res.rowcount == 0:
                return False, f"User ID {user_id} not found."
        state_label = "Activated" if is_active else "Deactivated"
        self.log_admin_action(actor_email, f"{state_label} user #{user_id}")
        return True, f"{state_label} user #{user_id}."

    def get_user_activity_dataframe(self, limit: int = 100) -> pd.DataFrame:
        """Return recent user activity rows if available."""
        columns = ["ID", "User ID", "Activity Type", "Details", "IP Address", "Created At"]
        if not table_exists(self.main_engine, "user_activity"):
            return pd.DataFrame(columns=columns)
        stmt = text("""
            SELECT
                id AS "ID",
                user_id AS "User ID",
                activity_type AS "Activity Type",
                activity_details AS "Details",
                ip_address AS "IP Address",
                created_at AS "Created At"
            FROM user_activity
            ORDER BY created_at DESC, id DESC
            LIMIT :lim
        """)
        with self.main_engine.connect() as conn:
            return pd.read_sql_query(stmt, conn, params={"lim": int(limit)})

    @staticmethod
    def export_dataframe_excel(df: pd.DataFrame, sheet_name: str = "Data") -> bytes:
        """Export any DataFrame cleanly to formatted XLSX bytes."""
        output = BytesIO()
        safe_sheet = sheet_name[:31] or "Data"
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name=safe_sheet, index=False)
            workbook = writer.book
            worksheet = writer.sheets[safe_sheet]
            header_format = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#D7E4BC",
                "border": 1,
            })
            for col_idx, col_name in enumerate(df.columns):
                worksheet.write(0, col_idx, col_name, header_format)
                values = df[col_name].tolist()
                max_val_len = max((len(str(v)) for v in values if pd.notnull(v)), default=0)
                max_len = max(max_val_len, len(str(col_name))) + 2
                worksheet.set_column(col_idx, col_idx, min(max_len, 50))
        output.seek(0)
        return output.getvalue()

    @staticmethod
    def export_dataframe_csv(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    @staticmethod
    def export_dataframe_json(df: pd.DataFrame) -> bytes:
        return df.to_json(orient="records", date_format="iso").encode("utf-8")
