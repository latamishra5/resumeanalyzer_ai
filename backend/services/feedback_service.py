"""Feedback database service (pure Python, UI-agnostic)."""

from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd

from backend.config.settings import FEEDBACK_DB_PATH


class FeedbackService:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else FEEDBACK_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.setup_database()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def setup_database(self):
        """Create feedback table if it doesn't exist"""
        conn = self._get_connection()
        try:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rating INTEGER,
                    usability_score INTEGER,
                    feature_satisfaction INTEGER,
                    missing_features TEXT,
                    improvement_suggestions TEXT,
                    user_experience TEXT,
                    timestamp DATETIME
                )
            ''')
            conn.commit()
        finally:
            conn.close()

    def save_feedback(self, feedback_data):
        """Save feedback to database"""
        conn = self._get_connection()
        try:
            c = conn.cursor()
            c.execute('''
                INSERT INTO feedback (
                    rating, usability_score, feature_satisfaction,
                    missing_features, improvement_suggestions,
                    user_experience, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback_data['rating'],
                feedback_data['usability_score'],
                feedback_data['feature_satisfaction'],
                feedback_data['missing_features'],
                feedback_data['improvement_suggestions'],
                feedback_data['user_experience'],
                datetime.now(),
            ))
            conn.commit()
        finally:
            conn.close()

    def get_feedback_stats(self):
        """Get feedback statistics"""
        conn = self._get_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM feedback", conn)
        finally:
            conn.close()

        if df.empty:
            return {
                'avg_rating': 0,
                'avg_usability': 0,
                'avg_satisfaction': 0,
                'total_responses': 0,
            }

        return {
            'avg_rating': df['rating'].mean(),
            'avg_usability': df['usability_score'].mean(),
            'avg_satisfaction': df['feature_satisfaction'].mean(),
            'total_responses': len(df),
        }
