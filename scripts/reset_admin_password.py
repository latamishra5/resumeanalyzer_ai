#!/usr/bin/env python3
"""
Admin Password Reset Script for Resume Analyzer AI
This script will remove existing admin credentials and create a new admin account.
"""

from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.database.connection import get_database_connection


def reset_admin_password():
    """Reset admin password by removing old admin and creating new one"""

    conn = get_database_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM admin")
        print("Old admin records deleted successfully.")

        print("\n" + "=" * 50)
        print("CREATE NEW ADMIN ACCOUNT")
        print("=" * 50)

        email = input("Enter admin email: ").strip()
        while not email:
            print("Email cannot be empty!")
            email = input("Enter admin email: ").strip()

        password = input("Enter new admin password: ").strip()
        while not password or len(password) < 4:
            print("Password must be at least 4 characters long!")
            password = input("Enter new admin password: ").strip()

        confirm_password = input("Confirm password: ").strip()
        while password != confirm_password:
            print("Passwords do not match!")
            confirm_password = input("Confirm password: ").strip()

        cursor.execute("INSERT INTO admin (email, password) VALUES (?, ?)", (email, password))
        conn.commit()

        print(f"\n{'=' * 50}")
        print("ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print(f"{'=' * 50}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"{'=' * 50}")
        print("\nYou can now login with these credentials.")
        print("Please keep your password safe!")

        cursor.execute(
            "INSERT INTO admin_logs (admin_email, action) VALUES (?, ?)",
            (email, "Password reset - New admin created"),
        )
        conn.commit()

    except Exception as e:
        print(f"Error resetting admin password: {str(e)}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    reset_admin_password()
