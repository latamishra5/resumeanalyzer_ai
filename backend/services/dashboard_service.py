"""Dashboard data and analytics service (pure Python, SQLite + PostgreSQL compatible)."""

import ast
from collections import Counter
from datetime import datetime, timedelta, timezone
from io import BytesIO
import logging

import pandas as pd
from sqlalchemy import text

from backend.database.connection import _active_engine, _coerce_user_id
from backend.database.db import get_storage_size_label

logger = logging.getLogger(__name__)


def _ts_param(engine, dt: datetime):
    """Format naive UTC datetimes as strings on SQLite to match CURRENT_TIMESTAMP."""
    if engine.dialect.name == "sqlite":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


def _parse_skills_field(raw_skills) -> list[str]:
    """Parse stored skill values (comma-separated string or serialized list)."""
    if not raw_skills:
        return []
    text_val = str(raw_skills).strip()
    if not text_val:
        return []
    if text_val.startswith("[") and text_val.endswith("]"):
        try:
            parsed = ast.literal_eval(text_val)
            if isinstance(parsed, (list, tuple, set)):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    return [part.strip(" []\"'") for part in text_val.split(",") if part.strip(" []\"'")]


def _categorize_skill(skill: str) -> str:
    lower = skill.lower()
    if any(k in lower for k in ("python", "java", "javascript", "c++", "programming")):
        return "Programming"
    if any(k in lower for k in ("sql", "database", "mongodb")):
        return "Database"
    if any(k in lower for k in ("aws", "cloud", "azure")):
        return "Cloud"
    if any(k in lower for k in ("agile", "scrum", "management")):
        return "Management"
    return "Other"


class DashboardService:
    def _get_engine(self):
        return _active_engine()

    def get_resume_metrics(self, user_id=None):
        """Get resume-related metrics from database (optionally scoped to user_id)."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        metrics = {}
        user_filter = "AND rd.user_id = :uid" if uid is not None else ""
        stmt = text(f"""
            SELECT
                COUNT(DISTINCT rd.id) AS total_resumes,
                AVG(ra.ats_score) AS avg_ats_score,
                AVG(ra.keyword_match_score) AS avg_keyword_score,
                COUNT(DISTINCT CASE WHEN ra.ats_score >= 70 THEN rd.id END) AS high_scoring
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
            WHERE rd.created_at >= :start_dt {user_filter}
        """)
        with engine.connect() as conn:
            for period, start_date in (
                ("Today", start_of_day),
                ("This Week", start_of_week),
                ("This Month", start_of_month),
                ("All Time", datetime(2000, 1, 1)),
            ):
                params = {"start_dt": _ts_param(engine, start_date)}
                if uid is not None:
                    params["uid"] = uid
                row = conn.execute(stmt, params).fetchone()
                if row:
                    metrics[period] = {
                        "total": int(row[0] or 0),
                        "ats_score": round(float(row[1] or 0), 1),
                        "keyword_score": round(float(row[2] or 0), 1),
                        "high_scoring": int(row[3] or 0),
                    }
                else:
                    metrics[period] = {"total": 0, "ats_score": 0, "keyword_score": 0, "high_scoring": 0}
        return metrics

    def get_skill_distribution(self, user_id=None):
        """Get skill category counts cleanly across SQLite and PostgreSQL."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        counter = Counter()
        sql = "SELECT skills FROM resume_data WHERE skills IS NOT NULL"
        params = {}
        if uid is not None:
            sql += " AND user_id = :uid"
            params["uid"] = uid
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        for (raw_skills,) in rows:
            for skill in _parse_skills_field(raw_skills):
                counter[_categorize_skill(skill)] += 1

        if not counter:
            return [], []
        ordered = counter.most_common()
        return [c for c, _ in ordered], [n for _, n in ordered]

    def get_weekly_trends(self, user_id=None):
        """Get 7-day daily submission counts cleanly across SQLite and PostgreSQL."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        days = [(now - timedelta(days=x)).date() for x in range(6, -1, -1)]
        cutoff = datetime.combine(days[0], datetime.min.time())

        counts_by_day = Counter()
        sql = "SELECT created_at FROM resume_data WHERE created_at >= :cutoff"
        params = {"cutoff": _ts_param(engine, cutoff)}
        if uid is not None:
            sql += " AND user_id = :uid"
            params["uid"] = uid
        with engine.connect() as conn:
            rows = conn.execute(text(sql), params).fetchall()
        for (created_at,) in rows:
            day_key = str(created_at)[:10]
            counts_by_day[day_key] += 1

        labels = [d.strftime("%Y-%m-%d")[-3:] for d in days]
        values = [counts_by_day.get(d.strftime("%Y-%m-%d"), 0) for d in days]
        return labels, values

    def get_job_category_stats(self, user_id=None):
        """Get submission count and ATS pass rate by target category."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        where_clause = "WHERE rd.user_id = :uid" if uid is not None else ""
        params = {"uid": uid} if uid is not None else {}
        stmt = text(f"""
            SELECT
                COALESCE(rd.target_category, 'Other') AS category,
                COUNT(*) AS cnt,
                AVG(CASE WHEN ra.ats_score >= 70 THEN 1.0 ELSE 0.0 END) * 100.0 AS success_rate
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
            {where_clause}
            GROUP BY category
            ORDER BY cnt DESC
            LIMIT 5
        """)
        with engine.connect() as conn:
            rows = conn.execute(stmt, params).fetchall()
        return [r[0] for r in rows], [round(float(r[2] or 0), 1) for r in rows]

    def get_resume_data(self, user_id=None):
        """Get resume data joined with analysis metrics."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        where_clause = "WHERE r.user_id = :uid" if uid is not None else ""
        params = {"uid": uid} if uid is not None else {}
        try:
            stmt = text(f"""
                SELECT
                    r.id, r.name, r.email, r.phone, r.linkedin, r.github, r.portfolio,
                    r.target_role, r.target_category, r.created_at,
                    a.ats_score, a.keyword_match_score, a.format_score, a.section_score
                FROM resume_data r
                LEFT JOIN resume_analysis a ON r.id = a.resume_id
                {where_clause}
                ORDER BY r.created_at DESC
            """)
            with engine.connect() as conn:
                return [tuple(r) for r in conn.execute(stmt, params).fetchall()]
        except Exception as exc:
            logger.exception("Error fetching resume data: %s", exc)
            return []

    def _fetch_export_dataframe(self, user_id=None) -> pd.DataFrame:
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        where_clause = "WHERE rd.user_id = :uid" if uid is not None else ""
        params = {"uid": uid} if uid is not None else {}
        stmt = text(f"""
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
            {where_clause}
        """)
        with engine.connect() as conn:
            return pd.read_sql_query(stmt, conn, params=params)

    def export_to_excel(self, user_id=None):
        """Export data to formatted Excel bytes (xlsxwriter)."""
        df = self._fetch_export_dataframe(user_id=user_id)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Resume Data", index=False)
            workbook = writer.book
            worksheet = writer.sheets["Resume Data"]
            header_format = workbook.add_format({
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#D7E4BC",
                "border": 1,
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            for i, col in enumerate(df.columns):
                max_val_len = max((len(str(v)) for v in df[col].tolist() if pd.notnull(v)), default=0)
                max_length = max(max_val_len, len(str(col))) + 2
                worksheet.set_column(i, i, min(max_length, 50))
        output.seek(0)
        return output.getvalue()

    def export_to_openpyxl_excel(self):
        """Export resume data to Excel using openpyxl."""
        try:
            df = self._fetch_export_dataframe()
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Resume Data")
            return output.getvalue()
        except Exception as exc:
            logger.exception("Error exporting to Excel: %s", exc)
            return None

    def export_to_csv(self):
        """Export data to CSV bytes."""
        return self._fetch_export_dataframe().to_csv(index=False).encode("utf-8")

    def export_to_json(self):
        """Export data to JSON records."""
        engine = self._get_engine()
        stmt = text("""
            SELECT rd.*, ra.*
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """)
        with engine.connect() as conn:
            df = pd.read_sql_query(stmt, conn)
        return df.to_json(orient="records", date_format="iso")

    def get_database_stats(self):
        """Get database record counts and storage usage."""
        engine = self._get_engine()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        with engine.connect() as conn:
            total_resumes = conn.execute(text("SELECT COUNT(*) FROM resume_data")).scalar() or 0
            today_submissions = conn.execute(
                text("SELECT COUNT(*) FROM resume_data WHERE created_at >= :start_dt"),
                {"start_dt": _ts_param(engine, start_of_day)},
            ).scalar() or 0
        return {
            "total_resumes": int(total_resumes),
            "today_submissions": int(today_submissions),
            "storage_size": get_storage_size_label(engine),
        }

    @staticmethod
    def _trend_entry(change: float) -> dict:
        return {
            "value": abs(round(float(change or 0), 1)),
            "icon": "↑" if (change or 0) >= 0 else "↓",
            "class": "trend-up" if (change or 0) >= 0 else "trend-down",
        }

    def get_trend_indicators(self, user_id=None):
        """Get 7-day trend indicators cleanly across SQLite and PostgreSQL."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        cutoff_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
        cutoff = _ts_param(engine, cutoff_dt)
        indicators = {}
        rd_and_uid = "AND user_id = :uid" if uid is not None else ""
        rd_where_uid = "WHERE user_id = :uid" if uid is not None else ""
        base_params = {"cutoff": cutoff}
        uid_params = {"uid": uid} if uid is not None else {}
        if uid is not None:
            base_params["uid"] = uid

        with engine.connect() as conn:
            # 1. Resumes count delta
            try:
                total_res = conn.execute(text(f"SELECT COUNT(*) FROM resume_data {rd_where_uid}"), uid_params).scalar() or 0
                old_res = conn.execute(
                    text(f"SELECT COUNT(*) FROM resume_data WHERE created_at < :cutoff {rd_and_uid}"),
                    base_params,
                ).scalar() or 0
                change = ((total_res - old_res) * 100.0 / old_res) if old_res else 0.0
                indicators["resumes"] = self._trend_entry(change)
            except Exception:
                indicators["resumes"] = {"value": 0, "icon": "→", "class": "trend-neutral"}

            # 2. Average ATS delta
            ra_join = "FROM resume_analysis ra JOIN resume_data rd ON rd.id = ra.resume_id"
            ra_uid_where = "WHERE rd.user_id = :uid" if uid is not None else ""
            ra_uid_and = "AND rd.user_id = :uid" if uid is not None else ""
            try:
                cur_ats = conn.execute(text(f"SELECT AVG(ra.ats_score) {ra_join} {ra_uid_where}"), uid_params).scalar()
                old_ats = conn.execute(
                    text(f"SELECT AVG(ra.ats_score) {ra_join} WHERE ra.created_at < :cutoff {ra_uid_and}"),
                    base_params,
                ).scalar()
                change = ((cur_ats - old_ats) * 100.0 / old_ats) if (cur_ats is not None and old_ats) else 0.0
                indicators["ats"] = self._trend_entry(change)
            except Exception:
                indicators["ats"] = {"value": 0, "icon": "→", "class": "trend-neutral"}

            # 3. High performing count delta
            try:
                cur_hi = conn.execute(
                    text(f"SELECT COUNT(*) {ra_join} WHERE ra.ats_score >= 70 {ra_uid_and}"),
                    uid_params,
                ).scalar() or 0
                old_hi = conn.execute(
                    text(f"SELECT COUNT(*) {ra_join} WHERE ra.ats_score >= 70 AND ra.created_at < :cutoff {ra_uid_and}"),
                    base_params,
                ).scalar() or 0
                change = ((cur_hi - old_hi) * 100.0 / old_hi) if old_hi else 0.0
                indicators["high_performing"] = self._trend_entry(change)
            except Exception:
                indicators["high_performing"] = {"value": 0, "icon": "→", "class": "trend-neutral"}

            # 4. Success rate delta (percentage points)
            try:
                total_res = conn.execute(text(f"SELECT COUNT(*) FROM resume_data {rd_where_uid}"), uid_params).scalar() or 0
                old_res = conn.execute(
                    text(f"SELECT COUNT(*) FROM resume_data WHERE created_at < :cutoff {rd_and_uid}"),
                    base_params,
                ).scalar() or 0
                cur_hi = conn.execute(
                    text(f"SELECT COUNT(*) {ra_join} WHERE ra.ats_score >= 70 {ra_uid_and}"),
                    uid_params,
                ).scalar() or 0
                old_hi = conn.execute(
                    text(f"SELECT COUNT(*) {ra_join} WHERE ra.ats_score >= 70 AND ra.created_at < :cutoff {ra_uid_and}"),
                    base_params,
                ).scalar() or 0
                cur_rate = (cur_hi * 100.0 / total_res) if total_res else None
                old_rate = (old_hi * 100.0 / old_res) if old_res else None
                change = (cur_rate - old_rate) if (cur_rate is not None and old_rate is not None) else 0.0
                indicators["success_rate"] = self._trend_entry(change)
            except Exception:
                indicators["success_rate"] = {"value": 0, "icon": "→", "class": "trend-neutral"}

        return indicators

    def get_detailed_insights(self, user_id=None):
        """Get dynamic insights across SQLite and PostgreSQL."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        cutoff_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
        cutoff = _ts_param(engine, cutoff_dt)
        insights = []
        uid_where = "WHERE rd.user_id = :uid" if uid is not None else ""
        uid_and = "AND rd.user_id = :uid" if uid is not None else ""
        uid_params = {"uid": uid} if uid is not None else {}
        cutoff_params = {"cutoff": cutoff, **uid_params}

        with engine.connect() as conn:
            top_category = conn.execute(text(f"""
                SELECT rd.target_category, AVG(ra.ats_score) AS avg_score, COUNT(*) AS submission_count
                FROM resume_data rd
                JOIN resume_analysis ra ON rd.id = ra.resume_id
                {uid_where}
                GROUP BY rd.target_category
                ORDER BY avg_score DESC
                LIMIT 1
            """), uid_params).fetchone()
            if top_category:
                insights.append({
                    "title": "Top Performing Category",
                    "icon": "fas fa-trophy",
                    "description": f"{top_category[0]} leads with {float(top_category[1]):.1f}% average ATS score across {top_category[2]} submissions",
                    "trend_class": "trend-up",
                    "trend_icon": "↑",
                    "trend_value": f"{float(top_category[1]):.1f}%",
                })

            recent_score = conn.execute(
                text(
                    f"SELECT AVG(ra.ats_score) FROM resume_analysis ra "
                    f"JOIN resume_data rd ON rd.id = ra.resume_id "
                    f"WHERE ra.created_at >= :cutoff {uid_and}"
                ),
                cutoff_params,
            ).scalar()
            old_score = conn.execute(
                text(
                    f"SELECT AVG(ra.ats_score) FROM resume_analysis ra "
                    f"JOIN resume_data rd ON rd.id = ra.resume_id "
                    f"WHERE ra.created_at < :cutoff {uid_and}"
                ),
                cutoff_params,
            ).scalar()
            if recent_score is not None and old_score is not None:
                change = float(recent_score) - float(old_score)
                insights.append({
                    "title": "Weekly Trend",
                    "icon": "fas fa-chart-line",
                    "description": f"ATS scores have {'improved' if change >= 0 else 'decreased'} by {abs(change):.1f}% in the last week",
                    "trend_class": "trend-up" if change >= 0 else "trend-down",
                    "trend_icon": "↑" if change >= 0 else "↓",
                    "trend_value": f"{abs(change):.1f}%",
                })

            skill_rows = conn.execute(
                text(f"SELECT skills FROM resume_data rd WHERE rd.skills IS NOT NULL {uid_and}"),
                uid_params,
            ).fetchall()

        skill_counter = Counter()
        for (raw_skills,) in skill_rows:
            for skill in _parse_skills_field(raw_skills):
                skill_counter[skill] += 1

        top_skills = skill_counter.most_common(3)
        if top_skills:
            skills_text = ", ".join(f"{skill} ({count} resumes)" for skill, count in top_skills)
            insights.append({
                "title": "Top Skills",
                "icon": "fas fa-lightbulb",
                "description": f"Most in-demand skills: {skills_text}",
                "trend_class": "trend-up",
                "trend_icon": "↑",
                "trend_value": f"Top {len(top_skills)}",
            })

        return insights

    def get_quick_stats(self, user_id=None):
        """Get quick headline statistics for the dashboard."""
        engine = self._get_engine()
        uid = _coerce_user_id(user_id)
        uid_params = {"uid": uid} if uid is not None else {}
        rd_where = "WHERE user_id = :uid" if uid is not None else ""
        ra_join = "FROM resume_analysis ra JOIN resume_data rd ON rd.id = ra.resume_id"
        ra_where = "WHERE rd.user_id = :uid" if uid is not None else ""
        ra_and = "AND rd.user_id = :uid" if uid is not None else ""
        with engine.connect() as conn:
            total_resumes = conn.execute(
                text(f"SELECT COUNT(*) FROM resume_data {rd_where}"), uid_params
            ).scalar() or 0
            avg_ats = conn.execute(
                text(f"SELECT AVG(ra.ats_score) {ra_join} {ra_where}"), uid_params
            ).scalar() or 0
            high_performing = conn.execute(
                text(f"SELECT COUNT(*) {ra_join} WHERE ra.ats_score >= 70 {ra_and}"), uid_params
            ).scalar() or 0

        success_rate = (high_performing / total_resumes * 100.0) if total_resumes > 0 else 0.0
        return {
            "Total Resumes": f"{total_resumes:,}",
            "Avg ATS Score": f"{float(avg_ats):.1f}%",
            "High Performing": f"{high_performing:,}",
            "Success Rate": f"{success_rate:.1f}%",
        }
