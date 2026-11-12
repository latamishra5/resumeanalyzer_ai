"""Tests for backend.admin.service.AdminService."""

from sqlalchemy import text

from backend.admin.service import AdminService
from backend.database.db import ai_analysis_table, feedback_table, resume_analysis_table, resume_data_table, users_table, user_activity_table


def test_admin_service_full_lifecycle(tmp_path, monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    resume_db = tmp_path / "admin_resume.db"
    feedback_db = tmp_path / "admin_feedback.db"
    env_file = tmp_path / ".env"

    svc = AdminService(resume_db_path=resume_db, feedback_db_path=feedback_db, env_path=env_file)
    assert svc.has_any_admin() is False

    assert not svc.add_admin("invalid-email", "short")[0]
    ok, msg = svc.add_admin("boss@company.com", "StrongPass!1")
    assert ok, msg
    assert svc.has_any_admin() is True
    assert svc.verify_admin("BOSS@company.com", "StrongPass!1") is True
    assert svc.verify_admin("boss@company.com", "wrong") is False

    # Legacy plaintext admin row upgrades cleanly to scrypt
    with svc.main_engine.begin() as conn:
        conn.execute(text("INSERT INTO admin (email, password) VALUES ('legacy@company.com', 'Plaintext99')"))
    assert svc.verify_admin("legacy@company.com", "Plaintext99") is True
    with svc.main_engine.connect() as conn:
        upgraded = conn.execute(text("SELECT password FROM admin WHERE email = 'legacy@company.com'")).scalar()
    assert upgraded.startswith("scrypt$")

    assert svc.update_admin_password("legacy@company.com", "NewStrong!2", actor_email="boss@company.com")[0]
    assert svc.verify_admin("legacy@company.com", "NewStrong!2")
    assert not svc.delete_admin("boss@company.com", actor_email="boss@company.com")[0]
    assert svc.delete_admin("legacy@company.com", actor_email="boss@company.com")[0]

    # Seed resumes, analysis (with NULL text columns for pandas 3 export edge case), AI, users, feedback
    with svc.main_engine.begin() as conn:
        conn.execute(
            resume_data_table.insert().values(
                name="Alice Dev",
                email="alice@dev.io",
                phone="555-0100",
                linkedin=None,
                github=None,
                portfolio=None,
                target_role="Software Engineer",
                target_category="Tech",
                summary="Built APIs",
                skills="Python, SQL",
            )
        )
        conn.execute(
            resume_analysis_table.insert().values(
                resume_id=1,
                ats_score=86.0,
                keyword_match_score=80.0,
                format_score=90.0,
                section_score=85.0,
                missing_skills=None,
                recommendations="Add container examples",
            )
        )
        conn.execute(
            ai_analysis_table.insert().values(
                resume_id=1,
                model_used="Google Gemini",
                resume_score=88,
                job_role="Software Engineer",
            )
        )
        conn.execute(
            users_table.insert().values(
                username="alicedev",
                email="alice@dev.io",
                password_hash="scrypt$dummy",
                full_name="Alice Dev",
                phone="555-0100",
                is_active=1,
            )
        )
        conn.execute(
            user_activity_table.insert().values(
                user_id=1,
                activity_type="login",
                activity_details="Signed in",
                ip_address="127.0.0.1",
            )
        )

    from backend.database.db import init_all_tables
    init_all_tables(svc.feedback_engine, include_feedback=True)
    with svc.feedback_engine.begin() as fconn:
        fconn.execute(
            feedback_table.insert().values(
                rating=5,
                usability_score=5,
                feature_satisfaction=4,
                missing_features="PDF export",
                improvement_suggestions="Great UX",
                user_experience="Smooth",
            )
        )

    ov = svc.get_system_overview()
    assert ov["total_resumes"] == 1
    assert ov["ai_total_analyses"] == 1
    assert ov["total_feedback"] == 1
    assert ov["total_users"] == 1

    resumes_df = svc.get_all_resumes_dataframe()
    assert len(resumes_df) == 1
    assert len(svc.export_dataframe_excel(resumes_df)) > 100
    assert b"Alice Dev" in svc.export_dataframe_csv(resumes_df)
    assert b"Alice Dev" in svc.export_dataframe_json(resumes_df)

    ai_stats = svc.get_detailed_ai_stats()
    assert ai_stats["total_analyses"] == 1 and ai_stats["average_score"] == 88.0

    assert svc.set_user_active(1, False, "boss@company.com")[0]
    assert int(svc.get_users_dataframe().iloc[0]["Active"]) == 0
    assert len(svc.get_user_activity_dataframe()) == 1

    assert svc.delete_feedback_entry(1, "boss@company.com")[0]
    assert svc.get_feedback_dataframe().empty

    assert svc.delete_resume_record(1, "boss@company.com")[0]
    assert svc.get_all_resumes_dataframe().empty

    assert svc.reset_ai_stats("boss@company.com")[0]
    assert svc.get_detailed_ai_stats()["total_analyses"] == 0

    assert svc.clear_admin_logs("boss@company.com")[0]
    assert len(svc.get_admin_logs()) == 1
