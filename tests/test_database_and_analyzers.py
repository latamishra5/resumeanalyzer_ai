"""Tests for database URL normalization, connection, models, services, analyzers, and builder."""

from datetime import datetime, timedelta, timezone
import warnings

from backend.analyzers.ai_resume_analyzer import AIResumeAnalyzer, clean_markdown
from backend.analyzers.spacy_analyzer import ResumeAnalyzer as OptionalNlpAnalyzer
from backend.builders.resume_builder import ResumeBuilder
import backend.database.connection as conn_mod
from backend.database.db import normalize_database_url, resume_analysis_table, resume_data_table
import backend.database.models as models_mod
import backend.jobs.job_feed as job_feed_mod
from backend.jobs.webdriver_utils import get_chrome_version
from backend.services.dashboard_service import DashboardService, _parse_skills_field
from backend.services.feedback_service import FeedbackService


def test_normalize_database_url():
    assert normalize_database_url(None) is None
    assert normalize_database_url("   ") is None
    assert normalize_database_url("postgres://user:pw@host:5432/db").startswith("postgresql")
    assert normalize_database_url("sqlite:///resume_data.db") == "sqlite:///resume_data.db"


def test_connection_and_admin_delegation(tmp_path, monkeypatch):
    db_file = tmp_path / "conn.db"
    env_file = tmp_path / ".env"
    monkeypatch.setattr(conn_mod, "RESUME_DB_PATH", db_file)
    monkeypatch.setattr(conn_mod, "ENV_PATH", env_file)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    conn_mod.init_database()
    assert conn_mod.verify_admin("admin@example.com", "admin123") is False
    assert conn_mod.add_admin("admin1@test.local", "AdminPass!1") is True
    assert conn_mod.verify_admin("admin1@test.local", "AdminPass!1") is True

    monkeypatch.setenv("ADMIN_EMAIL", "envadmin@test.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "Env!Password")
    assert conn_mod.verify_admin("envadmin@test.local", "Env!Password") is True
    assert conn_mod.verify_admin("envadmin@test.local", "wrong") is False

    rid1 = conn_mod.save_resume_data({
        "personal_info": {"name": "Jane Doe", "email": "jane@test.local", "phone": "123456"},
        "summary": "Backend Engineer",
        "target_role": "Software Engineer",
        "target_category": "Software",
    })
    rid2 = conn_mod.save_resume_data({
        "personal_info": {"full_name": "John Smith", "email": "john@test.local", "phone": "654321"},
        "summary": "Data Scientist",
        "target_role": "Data Scientist",
        "target_category": "Data",
    })
    assert rid1 and rid2
    rows = conn_mod.get_all_resume_data()
    names = {r[1] for r in rows}
    assert {"Jane Doe", "John Smith"}.issubset(names)


def test_orm_models_dashboard_and_feedback_services(tmp_path, monkeypatch):
    orm_db = tmp_path / "orm.db"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mgr = models_mod.DatabaseManager(db_path=str(orm_db))
    dep_msgs = [str(w.message) for w in caught if "declarative_base" in str(w.message) or "utcnow" in str(w.message)]
    assert not dep_msgs
    mgr.engine.dispose()

    dash_db = tmp_path / "dash.db"
    env_file = tmp_path / ".env"
    monkeypatch.setattr(conn_mod, "RESUME_DB_PATH", dash_db)
    monkeypatch.setattr(conn_mod, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    conn_mod.init_database()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    old_ts = now - timedelta(days=10)
    new_ts = now - timedelta(days=1)
    engine = conn_mod._active_engine()
    with engine.begin() as conn:
        conn.execute(
            resume_data_table.insert().values(
                name="Old User",
                email="old@x.com",
                phone="111",
                target_role="Backend Dev",
                target_category="Tech",
                skills="Go, Docker",
                created_at=old_ts,
            )
        )
        conn.execute(
            resume_data_table.insert().values(
                name="New User",
                email="new@x.com",
                phone="222",
                target_role="ML Engineer",
                target_category="AI",
                skills='["PyTorch", "Rust", "Kubernetes"]',
                created_at=new_ts,
            )
        )
        conn.execute(
            resume_analysis_table.insert().values(
                resume_id=1, ats_score=55.0, keyword_match_score=50.0, format_score=60.0, section_score=60.0, created_at=old_ts
            )
        )
        conn.execute(
            resume_analysis_table.insert().values(
                resume_id=2, ats_score=88.0, keyword_match_score=85.0, format_score=90.0, section_score=90.0, created_at=new_ts
            )
        )

    assert _parse_skills_field('["PyTorch", "Rust"]') == ["PyTorch", "Rust"]
    svc = DashboardService()
    trends = svc.get_trend_indicators()
    assert {"resumes", "ats", "high_performing", "success_rate"}.issubset(trends.keys())
    insights = svc.get_detailed_insights()
    joined = " ".join(str(i) for i in insights)
    assert "Java" not in joined and "Express" not in joined
    assert len(svc.export_to_excel()) > 100

    fb = FeedbackService(db_path=tmp_path / "feedback.db")
    fb.save_feedback({
        "rating": 5,
        "usability_score": 4,
        "feature_satisfaction": 5,
        "missing_features": "None",
        "improvement_suggestions": "Fast UI",
        "user_experience": "Clean",
    })
    stats = fb.get_feedback_stats()
    assert stats["total_responses"] == 1 and stats["avg_rating"] == 5.0


def test_deterministic_ai_fallback_builder_and_webdriver(monkeypatch):
    assert clean_markdown("**Hello** _World_ *Items*") == "Hello World Items"

    monkeypatch.setenv("GOOGLE_API_KEY", "")
    ai = AIResumeAnalyzer()
    sample_resume = (
        "Jane Doe\njane@example.com\n555-123-4567\n"
        "Experience\nSoftware Engineer building Python APIs and SQL services.\n"
        "Education\nB.S. Computer Science\nSkills\nPython, SQL, Docker"
    )
    res1 = ai.analyze_resume(sample_resume, job_role="Software Engineer", role_info={"required_skills": ["Python", "SQL"]})
    res2 = ai.analyze_resume(sample_resume, job_role="Software Engineer", role_info={"required_skills": ["Python", "SQL"]})
    assert res1["score"] == res2["score"] and res1["ats_score"] == res2["ats_score"]
    assert res1["analysis_mode"] == "deterministic_fallback" and res1["fallback_used"] is True

    builder = ResumeBuilder()
    docx_buf = builder.generate_resume({
        "template": "Modern",
        "personal_info": {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-0199",
            "location": "Remote",
            "linkedin": "https://linkedin.com/in/janedoe",
            "portfolio": "https://janedoe.dev",
        },
        "summary": "Backend software engineer.",
        "experience": [{"company": "Acme", "position": "Engineer", "start_date": "2022", "end_date": "Present", "description": "APIs", "responsibilities": ["Built services"], "achievements": ["Cut latency 30%"]}],
        "education": [{"school": "State U", "degree": "B.S.", "field": "CS", "graduation_date": "2021", "gpa": "3.8", "achievements": []}],
        "projects": [],
        "skills": {"technical": ["Python", "SQL"], "soft": ["Leadership"], "languages": ["English"], "tools": ["Git"]},
    })
    assert len(docx_buf.getvalue()) > 1000

    chrome_ver = get_chrome_version()
    assert chrome_ver is None or (isinstance(chrome_ver, str) and chrome_ver.isdigit())


def test_structured_ai_gap_rewriter_pdf_builder_and_job_feed(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    ai = AIResumeAnalyzer()
    resume_txt = (
        "Alex Rivera\nalex@example.com\n+1 555-234-5678\nhttps://github.com/alex\n"
        "Summary\nBackend engineer with 4 years experience.\n"
        "Experience\n- Worked on Python FastAPI services\n"
        "Education\nB.S. Computer Science\nSkills\nPython, FastAPI, SQL"
    )
    jd_txt = "Seeking a Backend Engineer skilled in Python, FastAPI, Docker, Kubernetes, PostgreSQL."
    ai_res = ai.analyze_resume_with_gemini(resume_txt, job_description=jd_txt, job_role="Backend Engineer")
    assert ai_res["analysis_mode"] == "deterministic_fallback"
    structured = ai_res["structured"]
    assert "Python" in structured["matched_keywords"]
    assert any(k in structured["missing_keywords"] for k in ("Docker", "Kubernetes", "Postgresql"))
    assert ai_res["job_match_score"] == structured["keyword_match_score"]
    assert len(structured["bullet_rewrites"]) >= 1

    rewrites = ai.rewrite_resume_bullets("- Worked on API endpoints\n- Helped with testing", allow_llm=False)
    assert len(rewrites) == 2
    assert rewrites[0]["improved"].startswith("Engineered")

    builder = ResumeBuilder()
    sample_data = {
        "template": "Modern",
        "personal_info": {
            "full_name": "<script>alert(1)</script> Jane",
            "email": "jane@example.com",
            "phone": "555-0199",
            "location": "Remote",
        },
        "summary": "Platform Engineer & Architect",
        "experience": [{"company": "Acme", "position": "Engineer", "start_date": "2022", "end_date": "Present", "description": "APIs & Cloud", "responsibilities": ["Built FastAPI"], "achievements": ["40% faster"]}],
        "education": [{"school": "State U", "degree": "B.S.", "field": "CS", "graduation_date": "2021", "gpa": "3.8"}],
        "projects": [{"name": "Tracker", "technologies": "Python, SQL", "description": "Pipeline"}],
        "skills": {"technical": ["Python", "SQL"], "soft": [], "languages": ["English"], "tools": ["Docker"]},
    }
    preview_html = builder.render_resume_html_preview(sample_data)
    assert "<script>" not in preview_html and "&lt;script&gt;" in preview_html
    pdf_buf = builder.generate_resume_pdf(sample_data)
    assert pdf_buf is not None and pdf_buf.getvalue().startswith(b"%PDF")

    nlp_fallback = OptionalNlpAnalyzer().analyze_resume("Python AWS SQL engineer with 5 years experience.")
    assert nlp_fallback["metrics"]["experience_years"] == 5

    match = job_feed_mod.compute_job_match_score(
        ["Python", "SQL", "Docker"],
        job_title="Senior Python Backend Engineer",
        job_description="Build APIs using Python, Docker, Kubernetes, and PostgreSQL.",
        job_tags=["Python", "Docker", "Kubernetes"],
    )
    assert match["match_score"] > 0 and "Python" in match["matched_skills"] and "Kubernetes" in match["missing_skills"]

    class _MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "jobs": [
                    {
                        "title": "Python Engineer",
                        "company_name": "CloudCo",
                        "candidate_required_location": "Worldwide",
                        "job_type": "full_time",
                        "salary": "$120k",
                        "tags": ["Python", "SQL"],
                        "url": "https://remotive.com/jobs/123",
                        "publication_date": "2026-10-01T00:00:00",
                        "description": "<p>Build backend APIs with Python.</p>",
                    },
                    {
                        "title": "Bad Link Job",
                        "company_name": "XSSCo",
                        "url": "javascript:alert(1)",
                        "description": "ignore",
                    },
                ]
            }

    monkeypatch.setattr(job_feed_mod.requests, "get", lambda *a, **kw: _MockResponse())
    feed = job_feed_mod.fetch_remote_jobs("Python", limit=5)
    assert feed["error"] is None and len(feed["jobs"]) == 2
    assert feed["jobs"][0]["url"] == "https://remotive.com/jobs/123"
    assert feed["jobs"][1]["url"] == ""

    def _boom(*a, **kw):
        raise job_feed_mod.requests.RequestException("offline")

    monkeypatch.setattr(job_feed_mod.requests, "get", _boom)
    err_feed = job_feed_mod.fetch_remote_jobs("Python")
    assert err_feed["jobs"] == [] and err_feed["error"]
