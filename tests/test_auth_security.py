"""Tests for password security and AuthService user workflows."""

import hashlib
from sqlalchemy import create_engine, inspect, text

from backend.auth.auth_service import AuthService
from backend.auth.security import hash_password, verify_password
import backend.database.connection as conn_mod
import backend.database.db as db_mod
from backend.services.dashboard_service import DashboardService


def test_scrypt_and_legacy_password_verification():
    hashed = hash_password("S3cure!Pass")
    assert hashed.startswith("scrypt$")

    ok, needs_rehash = verify_password("S3cure!Pass", hashed)
    assert ok is True and needs_rehash is False

    ok_bad, _ = verify_password("wrong", hashed)
    assert ok_bad is False

    legacy_sha = hashlib.sha256(b"oldpass").hexdigest()
    ok_sha, rehash_sha = verify_password("oldpass", legacy_sha)
    assert ok_sha is True and rehash_sha is True

    ok_plain, rehash_plain = verify_password("plainpass", "plainpass")
    assert ok_plain is True and rehash_plain is True


def test_auth_service_register_login_and_legacy_upgrade(tmp_path):
    db_file = tmp_path / "auth.db"
    auth = AuthService(db_path=db_file)

    ok, msg = auth.register_user("alice", "alice@example.com", "Alice!234", full_name="Alice")
    assert ok, msg

    with auth.engine.connect() as conn:
        stored = conn.execute(
            text("SELECT password_hash FROM users WHERE username = 'alice'")
        ).scalar()
    assert stored.startswith("scrypt$")

    ok, msg, session = auth.login_user("alice", "Alice!234")
    assert ok and session and session["username"] == "alice", msg

    verified = auth.verify_session(session["session_token"])
    assert verified and verified["username"] == "alice"

    ok_bad, _, _ = auth.login_user("alice", "wrongpass")
    assert not ok_bad

    # Insert legacy unsalted SHA-256 user and confirm transparent scrypt upgrade on login
    legacy_hash = hashlib.sha256(b"Legacy!1").hexdigest()
    with auth.engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (username, email, password_hash, full_name, is_active) "
                "VALUES ('bob', 'bob@example.com', :ph, 'Bob', 1)"
            ),
            {"ph": legacy_hash},
        )

    ok_bob, _, bob_session = auth.login_user("bob", "Legacy!1")
    assert ok_bob and bob_session["username"] == "bob"

    with auth.engine.connect() as conn:
        upgraded = conn.execute(
            text("SELECT password_hash FROM users WHERE username = 'bob'")
        ).scalar()
    assert upgraded.startswith("scrypt$")

    ok_out, _ = auth.logout_user(session_token=session["session_token"], user_id=session["user_id"])
    assert ok_out and auth.verify_session(session["session_token"]) is None


def test_user_scoped_workspace_history_and_schema_migration(tmp_path, monkeypatch):
    legacy_db = tmp_path / "legacy_workspace.db"
    env_file = tmp_path / ".env"

    legacy_engine = create_engine(f"sqlite:///{legacy_db}")
    with legacy_engine.begin() as conn:
        conn.execute(text("CREATE TABLE resume_data (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, linkedin TEXT, github TEXT, portfolio TEXT, summary TEXT, target_role TEXT, target_category TEXT, education TEXT, experience TEXT, projects TEXT, skills TEXT, template TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        conn.execute(text("CREATE TABLE ai_analysis (id INTEGER PRIMARY KEY AUTOINCREMENT, resume_id INTEGER, model_used TEXT, resume_score INTEGER, job_role TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
    legacy_engine.dispose()

    monkeypatch.setattr(conn_mod, "RESUME_DB_PATH", legacy_db)
    monkeypatch.setattr(conn_mod, "ENV_PATH", env_file)
    monkeypatch.setattr(db_mod, "RESUME_DB_PATH", legacy_db)
    monkeypatch.setattr(db_mod, "ENV_PATH", env_file)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    conn_mod.init_database()
    insp = inspect(conn_mod._active_engine())
    assert "user_id" in {c["name"] for c in insp.get_columns("resume_data")}
    assert "user_id" in {c["name"] for c in insp.get_columns("ai_analysis")}

    auth = AuthService(db_path=legacy_db)
    assert auth.register_user("userone", "u1@test.local", "Pass!1234", full_name="User One")[0]
    assert auth.register_user("usertwo", "u2@test.local", "Pass!1234", full_name="User Two")[0]
    u1_id = auth.login_user("userone", "Pass!1234")[2]["user_id"]
    u2_id = auth.login_user("usertwo", "Pass!1234")[2]["user_id"]

    r1 = conn_mod.save_resume_data({
        "personal_info": {"full_name": "User One", "email": "u1@test.local", "phone": "111"},
        "target_role": "Backend Engineer",
        "target_category": "Software",
        "skills": ["Python", "SQL"],
    }, user_id=u1_id)
    r2 = conn_mod.save_resume_data({
        "personal_info": {"full_name": "User Two", "email": "u2@test.local", "phone": "222"},
        "target_role": "Data Analyst",
        "target_category": "Data",
        "skills": ["SQL"],
    }, user_id=u2_id)
    conn_mod.save_analysis_data(r1, {"ats_score": 82, "keyword_match_score": 80, "format_score": 85, "section_score": 80})
    conn_mod.save_analysis_data(r2, {"ats_score": 60, "keyword_match_score": 60, "format_score": 60, "section_score": 60})

    u1_hist = conn_mod.get_user_resumes_history(u1_id)
    assert len(u1_hist) == 1 and u1_hist[0]["target_role"] == "Backend Engineer"

    dash = DashboardService()
    u1_stats = dash.get_quick_stats(user_id=u1_id)
    global_stats = dash.get_quick_stats()
    assert u1_stats["Total Resumes"] == "1"
    assert global_stats["Total Resumes"] == "2"
