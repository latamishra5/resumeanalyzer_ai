"""Isolated Streamlit AppTest checks for Public Frontend and Backend Admin Portal."""

from pathlib import Path
import warnings

from sqlalchemy import text
from streamlit.testing.v1 import AppTest

import backend.admin.service as admin_svc_mod
import backend.database.connection as conn_mod
import backend.database.db as db_mod
from backend.database.db import ai_analysis_table, feedback_table, init_all_tables, resume_analysis_table, resume_data_table


def test_public_frontend_apptest_all_pages(tmp_path, monkeypatch):
    resume_db = tmp_path / "fe_resume.db"
    feedback_db = tmp_path / "fe_feedback.db"
    env_file = tmp_path / ".env"
    monkeypatch.setattr(conn_mod, "RESUME_DB_PATH", resume_db)
    monkeypatch.setattr(conn_mod, "ENV_PATH", env_file)
    monkeypatch.setattr(db_mod, "RESUME_DB_PATH", resume_db)
    monkeypatch.setattr(db_mod, "FEEDBACK_DB_PATH", feedback_db)
    monkeypatch.setattr(db_mod, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        at = AppTest.from_file("app.py", default_timeout=90)
        at.run(timeout=90)
        assert not at.exception and not at.error
        assert "is_admin" not in at.session_state
        assert len(at.sidebar.expander) == 0

        for slug in ("home", "resume_analyzer", "resume_builder", "dashboard", "job_search", "feedback", "about"):
            target = slug.replace("_", " ").upper()
            matched = [b for b in at.sidebar.button if target in b.label.upper()]
            assert matched, f"Missing nav button for {slug}"
            matched[0].click()
            at.run(timeout=90)
            assert not at.exception, [e.value for e in at.exception]
            assert not at.error, [e.value for e in at.error]
            assert at.session_state["page"] == slug

        at_qp = AppTest.from_file("app.py", default_timeout=90)
        at_qp.query_params["page"] = "analyzer"
        at_qp.run(timeout=90)
        assert not at_qp.exception and not at_qp.error
        assert at_qp.session_state["page"] == "resume_analyzer"

        # Account workflow in sidebar (Sign Up / Sign In buttons render without admin controls)
        at_auth = AppTest.from_file("app.py", default_timeout=90)
        at_auth.run(timeout=90)
        signin_btn = [b for b in at_auth.sidebar.button if b.label == "Sign In"]
        signup_btn = [b for b in at_auth.sidebar.button if b.label == "Sign Up"]
        assert signin_btn and signup_btn
        signup_btn[0].click()
        at_auth.run(timeout=90)
        assert at_auth.session_state["page"] == "signup" and not at_auth.exception
        signin_btn = [b for b in at_auth.sidebar.button if b.label == "Sign In"]
        signin_btn[0].click()
        at_auth.run(timeout=90)
        assert at_auth.session_state["page"] == "login" and not at_auth.exception

    dep_warnings = [w for w in caught if "use_container_width" in str(w.message) or "use_column_width" in str(w.message)]
    assert not dep_warnings, dep_warnings


def test_backend_admin_portal_apptest_all_sections(tmp_path, monkeypatch):
    resume_db = tmp_path / "portal_resume.db"
    feedback_db = tmp_path / "portal_feedback.db"
    env_file = tmp_path / ".env"

    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(admin_svc_mod, "ENV_PATH", env_file)

    orig_init = admin_svc_mod.AdminService.__init__

    def _isolated_init(self, resume_db_path=None, feedback_db_path=None, env_path=None, database_url=None):
        orig_init(
            self,
            resume_db_path=resume_db_path or resume_db,
            feedback_db_path=feedback_db_path or feedback_db,
            env_path=env_path or env_file,
            database_url=database_url,
        )

    monkeypatch.setattr(admin_svc_mod.AdminService, "__init__", _isolated_init)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        # First-time setup flow
        at = AppTest.from_file("backend/admin/app.py", default_timeout=90)
        at.run(timeout=90)
        assert not at.exception and not at.error
        assert any("First-Time Admin Setup" in s.value for s in at.subheader)
        at.text_input[0].set_value("admin@portal.test")
        at.text_input[1].set_value("PortalPass!123")
        at.text_input[2].set_value("PortalPass!123")
        at.button[0].click()
        at.run(timeout=90)
        assert not at.exception and not at.error
        assert at.session_state["admin_authenticated"] is True

        # Seed sample records and test login + 6 tabs + logout
        svc = admin_svc_mod.AdminService()
        init_all_tables(svc.feedback_engine, include_feedback=True)
        with svc.main_engine.begin() as conn:
            conn.execute(
                resume_data_table.insert().values(
                    name="Bob Builder", email="bob@test.io", phone="12345",
                    target_role="Data Scientist", target_category="Data", summary="ML engineer", skills="Python",
                )
            )
            conn.execute(
                resume_analysis_table.insert().values(
                    resume_id=1, ats_score=91.0, keyword_match_score=88.0, format_score=95.0, section_score=90.0
                )
            )
            conn.execute(
                ai_analysis_table.insert().values(
                    resume_id=1, model_used="Google Gemini", resume_score=92, job_role="Data Scientist"
                )
            )
        with svc.feedback_engine.begin() as fconn:
            fconn.execute(
                feedback_table.insert().values(
                    rating=5, usability_score=4, feature_satisfaction=5,
                    missing_features="None", improvement_suggestions="Nice portal", user_experience="Fast",
                )
            )

        at2 = AppTest.from_file("backend/admin/app.py", default_timeout=90)
        at2.run(timeout=90)
        assert any("Admin Sign In" in s.value for s in at2.subheader)

        at2.text_input[0].set_value("admin@portal.test")
        at2.text_input[1].set_value("PortalPass!123")
        at2.button[0].click()
        at2.run(timeout=90)
        assert at2.session_state["admin_authenticated"] is True

        for sec in (
            "Overview",
            "Resume Submissions",
            "AI Analytics",
            "User Feedback",
            "Registered Users",
            "Admin & Audit Logs",
        ):
            at2.sidebar.radio[0].set_value(sec)
            at2.run(timeout=90)
            assert not at2.exception, (sec, [e.value for e in at2.exception])
            assert not at2.error, (sec, [e.value for e in at2.error])

        logout_btn = [b for b in at2.sidebar.button if "Logout" in b.label][0]
        logout_btn.click()
        at2.run(timeout=90)
        assert at2.session_state["admin_authenticated"] is False

    dep_warnings = [w for w in caught if "use_container_width" in str(w.message) or "use_column_width" in str(w.message)]
    assert not dep_warnings, dep_warnings
