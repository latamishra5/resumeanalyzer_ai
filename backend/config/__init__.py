"""Configuration data and path settings."""

from .courses import (
    COURSES_BY_CATEGORY,
    INTERVIEW_VIDEOS,
    RESUME_VIDEOS,
    get_category_for_role,
    get_courses_for_role,
)
from .job_roles import JOB_ROLES
from .settings import (
    ASSETS_DIR,
    BACKEND_DIR,
    BASE_DIR,
    ENV_PATH,
    EXCEL_DATA_PATH,
    FEEDBACK_DB_PATH,
    FRONTEND_DIR,
    RESUME_DB_PATH,
    SCRIPTS_DIR,
    STYLE_CSS_PATH,
    STYLES_DIR,
)

__all__ = [
    "ASSETS_DIR",
    "BACKEND_DIR",
    "BASE_DIR",
    "COURSES_BY_CATEGORY",
    "ENV_PATH",
    "EXCEL_DATA_PATH",
    "FEEDBACK_DB_PATH",
    "FRONTEND_DIR",
    "INTERVIEW_VIDEOS",
    "JOB_ROLES",
    "RESUME_DB_PATH",
    "RESUME_VIDEOS",
    "SCRIPTS_DIR",
    "STYLE_CSS_PATH",
    "STYLES_DIR",
    "get_category_for_role",
    "get_courses_for_role",
]
