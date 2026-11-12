#!/usr/bin/env python3
"""
Admin Password Reset Script for Resume Analyzer AI
This script will remove existing admin credentials and create a new admin account.
"""

from getpass import getpass
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.admin.service import AdminService


def reset_admin_password():
    """Reset admin password by removing old admin and creating a hashed one."""
    service = AdminService()

    print("\n" + "=" * 50)
    print("CREATE NEW ADMIN ACCOUNT")
    print("=" * 50)

    email = input("Enter admin email: ").strip()
    while not email:
        print("Email cannot be empty!")
        email = input("Enter admin email: ").strip()

    password = getpass("Enter new admin password (min 8 chars): ").strip()
    while not password or len(password) < 8:
        print("Password must be at least 8 characters long!")
        password = getpass("Enter new admin password (min 8 chars): ").strip()

    confirm_password = getpass("Confirm password: ").strip()
    while password != confirm_password:
        print("Passwords do not match!")
        confirm_password = getpass("Confirm password: ").strip()

    ok, msg = service.replace_with_single_admin(email, password)
    if ok:
        service.log_admin_action(email, "Password reset - New admin created")
        print(f"\n{'=' * 50}")
        print("ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print(f"{'=' * 50}")
        print(f"Email: {email}")
        print(f"{'=' * 50}")
        print("\nSign in via the Backend Admin Portal (python run_admin.py).")
    else:
        print(f"Error resetting admin password: {msg}")


if __name__ == "__main__":
    reset_admin_password()
