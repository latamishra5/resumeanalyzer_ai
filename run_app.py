#!/usr/bin/env python3
"""
Run script for Resume Analyzer(AI)
This script handles Chrome/chromedriver setup and starts the application
"""

import os
import subprocess
import sys


def main():
    """Main function to set up chromedriver and run the application"""
    print("Starting Resume Analyzer(AI)...")

    root_dir = os.path.dirname(os.path.abspath(__file__))

    # Run the chromedriver setup script silently
    setup_script = os.path.join(root_dir, "scripts", "setup_chromedriver.py")

    if os.path.exists(setup_script):
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.run(
                    [sys.executable, setup_script],
                    stdout=devnull,
                    stderr=devnull,
                )
        except Exception:
            pass

    # Start the Streamlit application
    print("Starting application...")
    app_script = os.path.join(root_dir, "app.py")

    if os.path.exists(app_script):
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", app_script])
        except Exception as e:
            print(f"Error starting application: {str(e)}")
            sys.exit(1)
    else:
        print(f"Application script not found at {app_script}")
        sys.exit(1)


if __name__ == "__main__":
    main()
