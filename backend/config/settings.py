"""Centralized filesystem paths and settings for Resume Analyzer AI."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
STYLES_DIR = FRONTEND_DIR / "styles"
STYLE_CSS_PATH = STYLES_DIR / "style.css"
ASSETS_DIR = FRONTEND_DIR / "assets"

BACKEND_DIR = BASE_DIR / "backend"
SCRIPTS_DIR = BASE_DIR / "scripts"

RESUME_DB_PATH = BASE_DIR / "resume_data.db"
FEEDBACK_DB_PATH = BASE_DIR / "feedback.db"
EXCEL_DATA_PATH = BASE_DIR / "resume_data.xlsx"
ENV_PATH = BASE_DIR / ".env"
