"""
Authentication Service for Resume Analyzer AI
Handles user registration, login, and database-backed session management.
"""

from datetime import datetime, timedelta
import hashlib
import secrets
import sqlite3

from backend.config.settings import RESUME_DB_PATH


class AuthService:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or RESUME_DB_PATH)
        self.init_auth_database()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_auth_database(self):
        """Initialize authentication database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT,
            portfolio TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            verification_token TEXT,
            reset_token TEXT,
            reset_token_expires TIMESTAMP
        )
        ''')

        # Create user_sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Create user_activity table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            activity_details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        conn.commit()
        conn.close()

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_session_token(self):
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

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
        ip_address='unknown',
    ):
        """Register a new user"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email),
            )
            if cursor.fetchone():
                return False, "Username or email already exists"

            # Hash password
            password_hash = self.hash_password(password)

            # Insert new user
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, phone, linkedin, github, portfolio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, full_name, phone, linkedin, github, portfolio))

            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            conn = None

            # Log registration activity
            self.log_activity(user_id, "registration", f"User registered: {username}", ip_address=ip_address)

            return True, "Registration successful"

        except Exception as e:
            return False, f"Registration failed: {str(e)}"
        finally:
            if conn is not None:
                conn.close()

    def login_user(self, username_or_email, password, ip_address='unknown', user_agent='unknown'):
        """Authenticate user and create session.

        Returns:
            tuple[bool, str, dict | None]: (success, message, session_data)
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Find user
            cursor.execute('''
            SELECT id, username, email, password_hash, full_name, is_active
            FROM users
            WHERE (username = ? OR email = ?) AND is_active = 1
            ''', (username_or_email, username_or_email))

            user = cursor.fetchone()

            if not user:
                return False, "Invalid credentials", None

            user_id, username, email, stored_hash, full_name, is_active = user

            # Verify password
            if self.hash_password(password) != stored_hash:
                return False, "Invalid credentials", None

            # Create session
            session_token = self.generate_session_token()
            expires_at = datetime.now() + timedelta(hours=24)

            cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, session_token, expires_at, ip_address, user_agent))

            # Update last login
            cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
            conn = None

            # Log login activity
            self.log_activity(user_id, "login", f"User logged in: {username}", ip_address=ip_address)

            session_data = {
                'authenticated': True,
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'session_token': session_token,
            }
            return True, "Login successful", session_data

        except Exception as e:
            return False, f"Login failed: {str(e)}", None
        finally:
            if conn is not None:
                conn.close()

    def logout_user(self, session_token=None, user_id=None, ip_address='unknown'):
        """Logout user and invalidate session"""
        conn = None
        try:
            if session_token:
                conn = self._get_connection()
                cursor = conn.cursor()

                # Remove session
                cursor.execute('''
                DELETE FROM user_sessions WHERE session_token = ?
                ''', (session_token,))

                conn.commit()
                conn.close()
                conn = None

                # Log logout activity
                if user_id is not None:
                    self.log_activity(user_id, "logout", "User logged out", ip_address=ip_address)

            return True, "Logout successful"

        except Exception as e:
            return False, f"Logout failed: {str(e)}"
        finally:
            if conn is not None:
                conn.close()

    def verify_session(self, session_token):
        """Verify if a session token is valid and return user session payload or None."""
        if not session_token:
            return None

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check session
            cursor.execute('''
            SELECT u.id, u.username, u.email, u.full_name, s.expires_at
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP AND u.is_active = 1
            ''', (session_token,))

            session = cursor.fetchone()
            if not session:
                return None

            user_id, username, email, full_name, _expires_at = session
            return {
                'authenticated': True,
                'user_id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
            }

        except Exception:
            return None
        finally:
            if conn is not None:
                conn.close()

    def get_user_profile(self, user_id):
        """Get user profile information"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            SELECT username, email, full_name, phone, linkedin, github, portfolio, created_at, last_login
            FROM users WHERE id = ?
            ''', (user_id,))

            user = cursor.fetchone()

            if user:
                return {
                    'username': user[0],
                    'email': user[1],
                    'full_name': user[2],
                    'phone': user[3],
                    'linkedin': user[4],
                    'github': user[5],
                    'portfolio': user[6],
                    'created_at': user[7],
                    'last_login': user[8],
                }
            return None

        except Exception:
            return None
        finally:
            if conn is not None:
                conn.close()

    def update_user_profile(self, user_id, full_name=None, phone=None, linkedin=None, github=None, portfolio=None):
        """Update user profile"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            UPDATE users
            SET full_name = ?, phone = ?, linkedin = ?, github = ?, portfolio = ?
            WHERE id = ?
            ''', (full_name, phone, linkedin, github, portfolio, user_id))

            conn.commit()
            return True, "Profile updated successfully"

        except Exception as e:
            return False, f"Profile update failed: {str(e)}"
        finally:
            if conn is not None:
                conn.close()

    def change_password(self, user_id, current_password, new_password):
        """Change user password"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get current password hash
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()

            if not result:
                return False, "User not found"

            current_hash = result[0]

            # Verify current password
            if self.hash_password(current_password) != current_hash:
                return False, "Current password is incorrect"

            # Update password
            new_hash = self.hash_password(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))

            conn.commit()
            return True, "Password changed successfully"

        except Exception as e:
            return False, f"Password change failed: {str(e)}"
        finally:
            if conn is not None:
                conn.close()

    def log_activity(self, user_id, activity_type, activity_details=None, ip_address='unknown'):
        """Log user activity"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_details, ip_address)
            VALUES (?, ?, ?, ?)
            ''', (user_id, activity_type, activity_details, ip_address))

            conn.commit()
        except Exception:
            pass  # Don't fail if logging fails
        finally:
            if conn is not None:
                conn.close()

    def get_user_activity(self, user_id, limit=50):
        """Get user activity history"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            SELECT activity_type, activity_details, created_at
            FROM user_activity
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            ''', (user_id, limit))

            activities = cursor.fetchall()

            return [
                {
                    'type': activity[0],
                    'details': activity[1],
                    'timestamp': activity[2],
                }
                for activity in activities
            ]

        except Exception:
            return []
        finally:
            if conn is not None:
                conn.close()

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
            DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP
            ''')

            conn.commit()
        except Exception:
            pass  # Don't fail if cleanup fails
        finally:
            if conn is not None:
                conn.close()


AuthManager = AuthService
