"""Feedback database service (pure Python, supports SQLite & PostgreSQL)."""

from datetime import datetime, timezone
import logging

import pandas as pd
from sqlalchemy import text

from backend.database.db import feedback_table, get_engine, init_all_tables, table_exists

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self, db_path=None, database_url=None):
        self.db_path = db_path
        self.database_url = database_url
        self.engine = get_engine(db_url=database_url, db_path=db_path, role="feedback")
        self.setup_database()

    def setup_database(self):
        """Create feedback table if it doesn't exist."""
        init_all_tables(self.engine, include_feedback=True)

    def save_feedback(self, feedback_data):
        """Save feedback to database."""
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        with self.engine.begin() as conn:
            conn.execute(
                feedback_table.insert().values(
                    rating=feedback_data["rating"],
                    usability_score=feedback_data["usability_score"],
                    feature_satisfaction=feedback_data["feature_satisfaction"],
                    missing_features=feedback_data["missing_features"],
                    improvement_suggestions=feedback_data["improvement_suggestions"],
                    user_experience=feedback_data["user_experience"],
                    timestamp=now_utc,
                )
            )

    def get_feedback_stats(self):
        """Get feedback statistics."""
        if not table_exists(self.engine, "feedback"):
            return {
                "avg_rating": 0,
                "avg_usability": 0,
                "avg_satisfaction": 0,
                "total_responses": 0,
            }

        with self.engine.connect() as conn:
            df = pd.read_sql_query(text("SELECT * FROM feedback"), conn)

        if df.empty:
            return {
                "avg_rating": 0,
                "avg_usability": 0,
                "avg_satisfaction": 0,
                "total_responses": 0,
            }

        return {
            "avg_rating": float(df["rating"].mean()),
            "avg_usability": float(df["usability_score"].mean()),
            "avg_satisfaction": float(df["feature_satisfaction"].mean()),
            "total_responses": int(len(df)),
        }
