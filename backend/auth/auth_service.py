"""User authentication, session management, and profile service (SQLite + PostgreSQL)."""

from datetime import datetime, timedelta, timezone
import logging
import re
import secrets

from sqlalchemy import text

from backend.auth.security import hash_password as _hash_password, verify_password as _verify_password
from backend.database.db import (
    get_engine,
    init_all_tables,
    user_activity_table,
    user_sessions_table,
    users_table,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _ts_param(engine, dt: datetime):
    if engine.dialect.name == "sqlite":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt


class AuthService:
    def __init__(self, db_path=None, database_url=None):
        self.db_path = str(db_path) if db_path else None
        self.database_url = database_url
        self.engine = get_engine(db_url=database_url, db_path=db_path, role="main")
        self.init_auth_tables()

    def init_auth_tables(self):
        """Initialize authentication tables."""
        init_all_tables(self.engine, include_feedback=(self.engine.dialect.name != "sqlite"))

    @staticmethod
    def hash_password(password):
        """Hash password using salted scrypt."""
        return _hash_password(password)

    @staticmethod
    def generate_session_token():
        """Generate a cryptographically secure session token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_email(email):
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password):
        """Validate password strength."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        return True, "Password is strong"

    def register_user(
        self,
        username,
        email,
        password,
        full_name=None,
        phone=None,
        linkedin=None,
        github=None,
        portfolio=None,
        ip_address="unknown",
    ):
        """Register a new user."""
        try:
            with self.engine.begin() as conn:
                existing = conn.execute(
                    text("SELECT id FROM users WHERE username = :u OR email = :e"),
                    {"u": username, "e": email},
                ).fetchone()
                if existing:
                    return False, "Username or email already exists"

                password_hash = self.hash_password(password)
                res = conn.execute(
                    users_table.insert().values(
                        username=username,
                        email=email,
                        password_hash=password_hash,
                        full_name=full_name,
                        phone=phone,
                        linkedin=linkedin,
                        github=github,
                        portfolio=portfolio,
                    )
                )
                user_id = res.inserted_primary_key[0]

            self.log_activity(user_id, "registration", f"User registered: {username}", ip_address=ip_address)
            return True, "Registration successful"
        except Exception as exc:
            logger.exception("Registration failed: %s", exc)
            return False, f"Registration failed: {str(exc)}"

    def login_user(self, username_or_email, password, ip_address="unknown", user_agent="unknown"):
        """Authenticate user and create session."""
        try:
            with self.engine.begin() as conn:
                user = conn.execute(
                    text("""
                        SELECT id, username, email, password_hash, full_name, is_active
                        FROM users
                        WHERE (username = :ident OR email = :ident) AND is_active = 1
                    """),
                    {"ident": username_or_email},
                ).fetchone()

                if not user:
                    return False, "Invalid credentials", None

                user_id, username, email, stored_hash, full_name, _is_active = user
                is_valid, needs_rehash = _verify_password(password, stored_hash)
                if not is_valid:
                    return False, "Invalid credentials", None

                if needs_rehash:
                    conn.execute(
                        text("UPDATE users SET password_hash = :ph WHERE id = :uid"),
                        {"ph": _hash_password(password), "uid": user_id},
                    )

                session_token = self.generate_session_token()
                now_utc = _utc_now()
                expires_at = now_utc + timedelta(hours=24)

                conn.execute(
                    user_sessions_table.insert().values(
                        user_id=user_id,
                        session_token=session_token,
                        expires_at=expires_at,
                        ip_address=ip_address,
                        user_agent=user_agent,
                    )
                )
                conn.execute(
                    text("UPDATE users SET last_login = :now WHERE id = :uid"),
                    {"now": _ts_param(self.engine, now_utc), "uid": user_id},
                )

            self.log_activity(user_id, "login", f"User logged in: {username}", ip_address=ip_address)
            return True, "Login successful", {
                "authenticated": True,
                "user_id": user_id,
                "username": username,
                "email": email,
                "full_name": full_name,
                "session_token": session_token,
            }
        except Exception as exc:
            logger.exception("Login failed: %s", exc)
            return False, f"Login failed: {str(exc)}", None

    def logout_user(self, session_token=None, user_id=None, ip_address="unknown"):
        """Logout user and invalidate session."""
        try:
            if session_token:
                with self.engine.begin() as conn:
                    conn.execute(
                        text("DELETE FROM user_sessions WHERE session_token = :tok"),
                        {"tok": session_token},
                    )
                if user_id is not None:
                    self.log_activity(user_id, "logout", "User logged out", ip_address=ip_address)
            return True, "Logout successful"
        except Exception as exc:
            logger.exception("Logout failed: %s", exc)
            return False, f"Logout failed: {str(exc)}"

    def verify_session(self, session_token):
        """Verify if a session token is valid and return user session payload or None."""
        if not session_token:
            return None
        try:
            now_param = _ts_param(self.engine, _utc_now())
            with self.engine.connect() as conn:
                session = conn.execute(
                    text("""
                        SELECT u.id, u.username, u.email, u.full_name, s.expires_at
                        FROM user_sessions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.session_token = :tok
                          AND s.expires_at > :now_dt
                          AND u.is_active = 1
                    """),
                    {"tok": session_token, "now_dt": now_param},
                ).fetchone()
            if not session:
                return None
            return {
                "authenticated": True,
                "user_id": session[0],
                "username": session[1],
                "email": session[2],
                "full_name": session[3],
            }
        except Exception:
            return None

    def get_user_profile(self, user_id):
        """Get user profile information."""
        try:
            with self.engine.connect() as conn:
                user = conn.execute(
                    text("""
                        SELECT username, email, full_name, phone, linkedin, github, portfolio, created_at, last_login
                        FROM users WHERE id = :uid
                    """),
                    {"uid": user_id},
                ).fetchone()
            if not user:
                return None
            return {
                "username": user[0],
                "email": user[1],
                "full_name": user[2],
                "phone": user[3],
                "linkedin": user[4],
                "github": user[5],
                "portfolio": user[6],
                "created_at": user[7],
                "last_login": user[8],
            }
        except Exception:
            return None

    def update_user_profile(self, user_id, full_name=None, phone=None, linkedin=None, github=None, portfolio=None):
        """Update user profile."""
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        UPDATE users
                        SET full_name = :fn, phone = :ph, linkedin = :li, github = :gh, portfolio = :pf
                        WHERE id = :uid
                    """),
                    {"fn": full_name, "ph": phone, "li": linkedin, "gh": github, "pf": portfolio, "uid": user_id},
                )
            return True, "Profile updated successfully"
        except Exception as exc:
            return False, f"Profile update failed: {str(exc)}"

    def change_password(self, user_id, current_password, new_password):
        """Change user password."""
        try:
            with self.engine.begin() as conn:
                row = conn.execute(
                    text("SELECT password_hash FROM users WHERE id = :uid"),
                    {"uid": user_id},
                ).fetchone()
                if not row:
                    return False, "User not found"
                is_valid, _needs_rehash = _verify_password(current_password, row[0])
                if not is_valid:
                    return False, "Current password is incorrect"
                conn.execute(
                    text("UPDATE users SET password_hash = :ph WHERE id = :uid"),
                    {"ph": self.hash_password(new_password), "uid": user_id},
                )
            return True, "Password changed successfully"
        except Exception as exc:
            return False, f"Password change failed: {str(exc)}"

    def log_activity(self, user_id, activity_type, activity_details=None, ip_address="unknown"):
        """Log user activity."""
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    user_activity_table.insert().values(
                        user_id=user_id,
                        activity_type=activity_type,
                        activity_details=activity_details,
                        ip_address=ip_address,
                    )
                )
        except Exception:
            pass

    def get_user_activity(self, user_id, limit=50):
        """Get user activity history."""
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("""
                        SELECT activity_type, activity_details, created_at
                        FROM user_activity
                        WHERE user_id = :uid
                        ORDER BY created_at DESC
                        LIMIT :lim
                    """),
                    {"uid": user_id, "lim": int(limit)},
                ).fetchall()
            return [{"type": r[0], "details": r[1], "timestamp": r[2]} for r in rows]
        except Exception:
            return []

    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            now_param = _ts_param(self.engine, _utc_now())
            with self.engine.begin() as conn:
                conn.execute(
                    text("DELETE FROM user_sessions WHERE expires_at < :now_dt"),
                    {"now_dt": now_param},
                )
        except Exception:
            pass


AuthManager = AuthService
