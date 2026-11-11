"""Dashboard data and analytics service (pure Python, UI-agnostic)."""

from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd

from backend.database.connection import get_database_connection


class DashboardService:
    def _get_connection(self):
        return get_database_connection(check_same_thread=False)

    def get_resume_metrics(self):
        """Get resume-related metrics from database"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            now = datetime.now()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_of_week = now - timedelta(days=now.weekday())
            start_of_month = now.replace(day=1)

            metrics = {}
            for period, start_date in [
                ('Today', start_of_day),
                ('This Week', start_of_week),
                ('This Month', start_of_month),
                ('All Time', datetime(2000, 1, 1)),
            ]:
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT rd.id) as total_resumes,
                        ROUND(AVG(ra.ats_score), 1) as avg_ats_score,
                        ROUND(AVG(ra.keyword_match_score), 1) as avg_keyword_score,
                        COUNT(DISTINCT CASE WHEN ra.ats_score >= 70 THEN rd.id END) as high_scoring
                    FROM resume_data rd
                    LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
                    WHERE rd.created_at >= ?
                """, (start_date.strftime('%Y-%m-%d %H:%M:%S'),))

                row = cursor.fetchone()
                if row:
                    metrics[period] = {
                        'total': row[0] or 0,
                        'ats_score': row[1] or 0,
                        'keyword_score': row[2] or 0,
                        'high_scoring': row[3] or 0,
                    }
                else:
                    metrics[period] = {
                        'total': 0,
                        'ats_score': 0,
                        'keyword_score': 0,
                        'high_scoring': 0,
                    }

            return metrics
        finally:
            conn.close()

    def get_skill_distribution(self):
        """Get skill distribution data"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                WITH RECURSIVE split(skill, rest) AS (
                    SELECT '', skills || ','
                    FROM resume_data
                    UNION ALL
                    SELECT
                        substr(rest, 0, instr(rest, ',')),
                        substr(rest, instr(rest, ',') + 1)
                    FROM split
                    WHERE rest <> ''
                ),
                SkillCategories AS (
                    SELECT
                        CASE
                            WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%python%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%java%' OR
                                 LOWER(TRIM(skill, '[]" ')) LIKE '%javascript%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%c++%' OR
                                 LOWER(TRIM(skill, '[]" ')) LIKE '%programming%' THEN 'Programming'
                            WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%sql%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%database%' OR
                                 LOWER(TRIM(skill, '[]" ')) LIKE '%mongodb%' THEN 'Database'
                            WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%aws%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%cloud%' OR
                                 LOWER(TRIM(skill, '[]" ')) LIKE '%azure%' THEN 'Cloud'
                            WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%agile%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%scrum%' OR
                                 LOWER(TRIM(skill, '[]" ')) LIKE '%management%' THEN 'Management'
                            ELSE 'Other'
                        END as category,
                        COUNT(*) as count
                    FROM split
                    WHERE skill <> ''
                    GROUP BY category
                )
                SELECT category, count
                FROM SkillCategories
                ORDER BY count DESC
            """)

            categories, counts = [], []
            for row in cursor.fetchall():
                categories.append(row[0])
                counts.append(row[1])

            return categories, counts
        finally:
            conn.close()

    def get_weekly_trends(self):
        """Get weekly submission trends"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now()
            dates = [(now - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(6, -1, -1)]

            submissions = []
            for date in dates:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM resume_data
                    WHERE DATE(created_at) = DATE(?)
                """, (date,))
                submissions.append(cursor.fetchone()[0])

            return [d[-3:] for d in dates], submissions
        finally:
            conn.close()

    def get_job_category_stats(self):
        """Get statistics by job category"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(target_category, 'Other') as category,
                    COUNT(*) as count,
                    ROUND(AVG(CASE WHEN ra.ats_score >= 70 THEN 1 ELSE 0 END) * 100, 1) as success_rate
                FROM resume_data rd
                LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
                GROUP BY category
                ORDER BY count DESC
                LIMIT 5
            """)

            categories, success_rates = [], []
            for row in cursor.fetchall():
                categories.append(row[0])
                success_rates.append(row[2] or 0)

            return categories, success_rates
        finally:
            conn.close()

    def get_resume_data(self):
        """Get all resume data"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT
                r.id,
                r.name,
                r.email,
                r.phone,
                r.linkedin,
                r.github,
                r.portfolio,
                r.target_role,
                r.target_category,
                r.created_at,
                a.ats_score,
                a.keyword_match_score,
                a.format_score,
                a.section_score
            FROM resume_data r
            LEFT JOIN resume_analysis a ON r.id = a.resume_id
            ORDER BY r.created_at DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching resume data: {str(e)}")
            return []
        finally:
            conn.close()

    def export_to_excel(self):
        """Export data to Excel format (xlsxwriter formatted)."""
        query = """
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        conn = self._get_connection()
        try:
            df = pd.read_sql_query(query, conn)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Resume Data', index=False)

                workbook = writer.book
                worksheet = writer.sheets['Resume Data']

                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1,
                })

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                for i, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max() if not df.empty else 0,
                        len(str(col)),
                    ) + 2
                    worksheet.set_column(i, i, min(max_length, 50))

            output.seek(0)
            return output.getvalue()
        finally:
            conn.close()

    def export_to_openpyxl_excel(self):
        """Export resume data to Excel using openpyxl."""
        query = """
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        conn = self._get_connection()
        try:
            df = pd.read_sql_query(query, conn)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')
            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()

    def export_to_csv(self):
        """Export data to CSV format"""
        query = """
            SELECT
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        conn = self._get_connection()
        try:
            df = pd.read_sql_query(query, conn)
            return df.to_csv(index=False).encode('utf-8')
        finally:
            conn.close()

    def export_to_json(self):
        """Export data to JSON format"""
        query = """
            SELECT
                rd.*, ra.*
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        conn = self._get_connection()
        try:
            df = pd.read_sql_query(query, conn)
            return df.to_json(orient='records', date_format='iso')
        finally:
            conn.close()

    def get_database_stats(self):
        """Get database statistics"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            stats = {}

            cursor.execute("SELECT COUNT(*) FROM resume_data")
            stats['total_resumes'] = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*)
                FROM resume_data
                WHERE DATE(created_at) = DATE('now')
            """)
            stats['today_submissions'] = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            size_bytes = page_count * page_size

            if size_bytes < 1024:
                stats['storage_size'] = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                stats['storage_size'] = f"{size_bytes/1024:.1f} KB"
            else:
                stats['storage_size'] = f"{size_bytes/(1024*1024):.1f} MB"

            return stats
        finally:
            conn.close()

    def get_admin_logs(self):
        """Get admin logs"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT admin_email, action, timestamp
            FROM admin_logs
            ORDER BY timestamp DESC
            ''')
            return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching admin logs: {str(e)}")
            return []
        finally:
            conn.close()

    def get_trend_indicators(self):
        """Get trend indicators for stats"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            indicators = {}

            for metric in ['resumes', 'ats', 'high_performing', 'success_rate']:
                try:
                    if metric == 'resumes':
                        cursor.execute("""
                            SELECT
                                (COUNT(*) - (
                                    SELECT COUNT(*)
                                    FROM resume_data
                                    WHERE created_at < date('now', '-7 days')
                                )) * 100.0 /
                                NULLIF((
                                    SELECT COUNT(*)
                                    FROM resume_data
                                    WHERE created_at < date('now', '-7 days')
                                ), 0)
                            FROM resume_data
                        """)
                        change = cursor.fetchone()[0] or 0
                    elif metric == 'ats':
                        cursor.execute("""
                            SELECT
                                (AVG(ats_score) - (
                                    SELECT AVG(ats_score)
                                    FROM resume_analysis
                                    WHERE created_at < date('now', '-7 days')
                                )) * 100.0 /
                                NULLIF((
                                    SELECT AVG(ats_score)
                                    FROM resume_analysis
                                    WHERE created_at < date('now', '-7 days')
                                ), 0)
                            FROM resume_analysis
                        """)
                        change = cursor.fetchone()[0] or 0
                    else:
                        indicators[metric] = {
                            'value': 0,
                            'icon': '→',
                            'class': 'trend-neutral',
                        }
                        continue

                    indicators[metric] = {
                        'value': abs(round(change, 1)),
                        'icon': '↑' if change >= 0 else '↓',
                        'class': 'trend-up' if change >= 0 else 'trend-down',
                    }
                except Exception:
                    indicators[metric] = {
                        'value': 0,
                        'icon': '→',
                        'class': 'trend-neutral',
                    }

            return indicators
        finally:
            conn.close()

    def get_detailed_insights(self):
        """Get detailed insights from the database"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            insights = []

            cursor.execute("""
                SELECT target_category, AVG(ats_score) as avg_score,
                       COUNT(*) as submission_count
                FROM resume_data rd
                JOIN resume_analysis ra ON rd.id = ra.resume_id
                GROUP BY target_category
                ORDER BY avg_score DESC
                LIMIT 1
            """)
            top_category = cursor.fetchone()
            if top_category:
                insights.append({
                    'title': 'Top Performing Category',
                    'icon': '🏆',
                    'description': f"{top_category[0]} leads with {top_category[1]:.1f}% average ATS score across {top_category[2]} submissions",
                    'trend_class': 'trend-up',
                    'trend_icon': '↑',
                    'trend_value': f"{top_category[1]:.1f}%",
                })

            cursor.execute("""
                SELECT
                    (SELECT AVG(ats_score) FROM resume_analysis
                     WHERE created_at >= date('now', '-7 days')) as recent_score,
                    (SELECT AVG(ats_score) FROM resume_analysis
                     WHERE created_at < date('now', '-7 days')) as old_score
            """)
            scores = cursor.fetchone()
            if scores and scores[0] and scores[1]:
                change = scores[0] - scores[1]
                insights.append({
                    'title': 'Weekly Trend',
                    'icon': '📈',
                    'description': f"ATS scores have {'improved' if change >= 0 else 'decreased'} by {abs(change):.1f}% in the last week",
                    'trend_class': 'trend-up' if change >= 0 else 'trend-down',
                    'trend_icon': '↑' if change >= 0 else '↓',
                    'trend_value': f"{abs(change):.1f}%",
                })

            cursor.execute("""
                WITH RECURSIVE
                split(skill, rest) AS (
                    SELECT '', skills || ','
                    FROM resume_data
                    WHERE skills IS NOT NULL
                    UNION ALL
                    SELECT
                        substr(rest, 0, instr(rest, ',')),
                        substr(rest, instr(rest, ',') + 1)
                    FROM split
                    WHERE rest <> ''
                ),
                cleaned_skills AS (
                    SELECT TRIM(REPLACE(REPLACE(skill, '[', ''), ']', '')) as skill
                    FROM split
                    WHERE skill <> ''
                )
                SELECT skill, COUNT(*) as count
                FROM cleaned_skills
                GROUP BY skill
                ORDER BY count DESC
                LIMIT 3
            """)
            top_skills = cursor.fetchall()
            if top_skills:
                if len(top_skills) >= 3:
                    skills_text = (
                        f"Most in-demand skills: Python ({top_skills[0][1]} resumes), "
                        f"Java ({top_skills[1][1]} resumes), Express ({top_skills[2][1]} resumes)"
                    )
                else:
                    skills_text = ", ".join(f"{skill} ({count} resumes)" for skill, count in top_skills)

                insights.append({
                    'title': 'Top Skills',
                    'icon': '💡',
                    'description': f"Most in-demand skills: {skills_text}",
                    'trend_class': 'trend-up',
                    'trend_icon': '🔝',
                    'trend_value': f"Top {len(top_skills)}",
                })

            return insights
        finally:
            conn.close()

    def get_quick_stats(self):
        """Get quick statistics for the dashboard"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM resume_data")
            total_resumes = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(ats_score) FROM resume_analysis")
            avg_ats = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM resume_analysis WHERE ats_score >= 70")
            high_performing = cursor.fetchone()[0]

            success_rate = (high_performing / total_resumes * 100) if total_resumes > 0 else 0

            return {
                "Total Resumes": f"{total_resumes:,}",
                "Avg ATS Score": f"{avg_ats:.1f}%",
                "High Performing": f"{high_performing:,}",
                "Success Rate": f"{success_rate:.1f}%",
            }
        finally:
            conn.close()
