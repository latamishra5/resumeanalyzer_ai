"""Feedback page view."""

import time
import streamlit as st

from backend.services.feedback_service import FeedbackService
from frontend.components.ui_components import apply_modern_styles, page_header


class FeedbackManager:
    def __init__(self, service=None):
        self.service = service or FeedbackService()

    def save_feedback(self, feedback_data):
        return self.service.save_feedback(feedback_data)

    def get_feedback_stats(self):
        return self.service.get_feedback_stats()

    def render_feedback_form(self):
        """Render the feedback form"""
        st.markdown("""
            <style>
            @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

            .feedback-container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                padding: 30px;
                border-radius: 20px;
                margin: 20px 0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }

            .feedback-header {
                color: #E0E0E0;
                font-size: 1.5em;
                font-weight: 600;
                margin-bottom: 25px;
                text-align: center;
                padding: 15px;
                background: linear-gradient(135deg, #4CAF50, #2196F3);
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
            }

            .feedback-section {
                margin: 20px 0;
                padding: 20px;
                border-radius: 15px;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }

            .feedback-section:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }

            .feedback-label {
                color: #E0E0E0;
                font-size: 1.1em;
                font-weight: 500;
                margin-bottom: 10px;
            }

            .star-rating {
                font-size: 24px;
                color: #FFD700;
                cursor: pointer;
                transition: transform 0.2s ease;
            }

            .star-rating:hover {
                transform: scale(1.1);
            }

            .rating-container {
                display: flex;
                align-items: center;
                gap: 10px;
                margin: 15px 0;
            }

            .submit-button {
                background: linear-gradient(135deg, #4CAF50, #2196F3);
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 1px;
                width: 100%;
                margin-top: 20px;
            }

            .submit-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(33, 150, 243, 0.3);
            }

            .textarea-container {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }

            .textarea-container textarea {
                width: 100%;
                min-height: 100px;
                background: transparent;
                border: none;
                color: #E0E0E0;
                font-size: 1em;
                resize: vertical;
            }
            </style>
            """, unsafe_allow_html=True)

        st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="feedback-header"><i class="fas fa-comment-dots"></i> Share Your Feedback</h2>', unsafe_allow_html=True)

        def _star_icons(count: int) -> str:
            return " ".join('<i class="fas fa-star" style="color: #f59e0b;"></i>' for _ in range(int(count)))

        # Overall Rating
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        st.markdown('<label class="feedback-label">Overall Experience Rating</label>', unsafe_allow_html=True)
        rating = st.slider("Overall Rating", 1, 5, 5, help="Rate your overall experience with the app", label_visibility="collapsed")
        st.markdown(f'<div class="rating-container">{_star_icons(rating)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Usability Score
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        st.markdown('<label class="feedback-label">How easy was it to use our app?</label>', unsafe_allow_html=True)
        usability_score = st.slider("Usability Score", 1, 5, 5, help="Rate the app\'s ease of use", label_visibility="collapsed")
        st.markdown(f'<div class="rating-container">{_star_icons(usability_score)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Feature Satisfaction
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        st.markdown('<label class="feedback-label">How satisfied are you with our features?</label>', unsafe_allow_html=True)
        feature_satisfaction = st.slider("Feature Satisfaction", 1, 5, 5, help="Rate your satisfaction with the app\'s features", label_visibility="collapsed")
        st.markdown(f'<div class="rating-container">{_star_icons(feature_satisfaction)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Text Feedback
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        st.markdown('<label class="feedback-label">What features would you like to see added?</label>', unsafe_allow_html=True)
        missing_features = st.text_area("Missing Features", placeholder="Share your feature requests...", label_visibility="collapsed")

        st.markdown('<label class="feedback-label">How can we improve?</label>', unsafe_allow_html=True)
        improvement_suggestions = st.text_area("Improvement Suggestions", placeholder="Your suggestions for improvement...", label_visibility="collapsed")

        st.markdown('<label class="feedback-label">Tell us about your experience</label>', unsafe_allow_html=True)
        user_experience = st.text_area("User Experience", placeholder="Share your experience with us...", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # Submit Button
        if st.button("Submit Feedback", key="submit_feedback", type="primary"):
            try:
                feedback_data = {
                    'rating': rating,
                    'usability_score': usability_score,
                    'feature_satisfaction': feature_satisfaction,
                    'missing_features': missing_features,
                    'improvement_suggestions': improvement_suggestions,
                    'user_experience': user_experience,
                }
                with st.spinner("Saving feedback..."):
                    self.save_feedback(feedback_data)

                st.success("Thank you for your feedback! It helps improve Resume Analyzer(AI).")
            except Exception as e:
                st.error(f"Error submitting feedback: {str(e)}")

    def render_feedback_stats(self):
        """Render feedback statistics"""
        stats = self.get_feedback_stats()

        st.markdown("""
            <div style="text-align: center; padding: 15px; background: linear-gradient(90deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.12)); border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: #E0E0E0;"><i class="fas fa-chart-bar"></i> Feedback Overview</h3>
            </div>
        """, unsafe_allow_html=True)

        cols = st.columns(4)
        metrics = [
            {"label": "Total Responses", "value": f"{stats['total_responses']:,}", "delta": '<i class="fas fa-users"></i>'},
            {"label": "Avg Rating", "value": f"{stats['avg_rating']:.1f}/5.0", "delta": '<i class="fas fa-star" style="color: #f59e0b;"></i>'},
            {"label": "Usability Score", "value": f"{stats['avg_usability']:.1f}/5.0", "delta": '<i class="fas fa-sliders-h"></i>'},
            {"label": "Satisfaction", "value": f"{stats['avg_satisfaction']:.1f}/5.0", "delta": '<i class="fas fa-smile"></i>'},
        ]

        for col, metric in zip(cols, metrics):
            col.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="color: #B0B0B0; font-size: 0.9em;">{metric['label']}</div>
                    <div style="font-size: 1.5em; color: #4CAF50; margin: 5px 0;">{metric['value']}</div>
                    <div style="color: #E0E0E0; font-size: 1.2em;">{metric['delta']}</div>
                </div>
            """, unsafe_allow_html=True)


def render_feedback_page():
    """Render the feedback page"""
    apply_modern_styles()

    page_header(
        "Feedback & Suggestions",
        "Help us improve by sharing your thoughts",
    )

    feedback_manager = FeedbackManager()
    form_tab, stats_tab = st.tabs(["Submit Feedback", "Feedback Stats"])

    with form_tab:
        feedback_manager.render_feedback_form()

    with stats_tab:
        feedback_manager.render_feedback_stats()
