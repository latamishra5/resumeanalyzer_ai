#!/usr/bin/env python3
"""
Create Admin Account for Resume Analyzer AI
Creates an admin user from ADMIN_EMAIL/ADMIN_PASSWORD env vars or interactive input.
"""

from getpass import getpass
import os
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

from backend.admin.service import AdminService
from backend.config.settings import ENV_PATH


def create_admin():
    """Create admin account with a salted scrypt password hash."""
    load_dotenv(ENV_PATH)
    load_dotenv()
    service = AdminService()

    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not email:
        email = input("Enter admin email: ").strip()
        while not email:
            print("Email cannot be empty!")
            email = input("Enter admin email: ").strip()

    if not password:
        password = getpass("Enter admin password (min 8 chars): ").strip()
        while len(password) < 8:
            print("Password must be at least 8 characters long!")
            password = getpass("Enter admin password (min 8 chars): ").strip()

    ok, msg = service.replace_with_single_admin(email, password)
    if ok:
        service.log_admin_action(email, "Admin account created via CLI")
        print("=" * 50)
        print("ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"Email: {email}")
        print("=" * 50)
        print("\nLaunch the Backend Admin Portal to sign in:")
        print("  python run_admin.py")
        print("  # or: streamlit run backend/admin/app.py --server.port 8502")
    else:
        print(f"Error creating admin: {msg}")


if __name__ == "__main__":
    create_admin()
