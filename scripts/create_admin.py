#!/usr/bin/env python3
"""
Create Default Admin Account for Resume Analyzer AI
This script will create a default admin account with simple credentials.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.database.connection import get_database_connection


def create_default_admin():
    """Create default admin account"""

    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM admin")

        default_email = "admin@resumeanalyzer.ai"
        default_password = "admin123"

        cursor.execute(
            "INSERT INTO admin (email, password) VALUES (?, ?)",
            (default_email, default_password),
        )
        conn.commit()

        print("=" * 50)
        print("DEFAULT ADMIN ACCOUNT CREATED!")
        print("=" * 50)
        print(f"Email: {default_email}")
        print(f"Password: {default_password}")
        print("=" * 50)
        print("\nUse these credentials to login in the sidebar.")

    except Exception as e:
        print(f"Error creating admin: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    create_default_admin()
