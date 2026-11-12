#!/usr/bin/env python3
"""
Launcher for the standalone Backend Admin Portal.
Runs on port 8502 by default so it stays separate from the public frontend (port 8501).
"""

import os
import subprocess
import sys


def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    admin_script = os.path.join(root_dir, "backend", "admin", "app.py")

    if not os.path.exists(admin_script):
        print(f"Admin portal script not found at {admin_script}")
        sys.exit(1)

    extra_args = sys.argv[1:]
    cmd = [sys.executable, "-m", "streamlit", "run", admin_script]
    if "--server.port" not in " ".join(extra_args):
        cmd.extend(["--server.port", "8502"])
    cmd.extend(extra_args)

    print("Starting Backend Admin Portal (default: http://localhost:8502)...")
    try:
        subprocess.run(cmd, check=False)
    except Exception as exc:
        print(f"Error starting Admin Portal: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
