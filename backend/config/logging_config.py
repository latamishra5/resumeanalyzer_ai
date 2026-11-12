"""Centralized logging configuration for Resume Analyzer(AI)."""

import logging
import os
import sys

from dotenv import load_dotenv

from backend.config.settings import ENV_PATH

_CONFIGURED = False


def configure_logging(force: bool = False) -> logging.Logger:
    """Configure root structured console logging using LOG_LEVEL and DEBUG env vars."""
    global _CONFIGURED
    if _CONFIGURED and not force:
        return logging.getLogger("resumeanalyzer")

    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=False)

    debug_flag = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}
    raw_level = os.getenv("LOG_LEVEL", "DEBUG" if debug_flag else "INFO").strip().upper()
    level = getattr(logging, raw_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(level)

    # Reduce third-party noise
    for noisy in ("urllib3", "selenium", "matplotlib", "google", "httpx", "watchdog"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))

    _CONFIGURED = True
    return logging.getLogger("resumeanalyzer")
