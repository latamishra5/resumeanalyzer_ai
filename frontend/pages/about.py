"""About page view."""

import base64
import os
import streamlit as st

from backend.config.settings import ASSETS_DIR
from frontend.components.ui_components import apply_modern_styles


def render_about():
    """Render the about page"""
    # Function to load image as base64
    def get_image_as_base64(file_path):
        try:
            with open(file_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode()
                return f"data:image/jpeg;base64,{encoded}"
        except Exception:
            return None

    # Get image path and convert to base64
    image_path = os.path.join(str(ASSETS_DIR), "124852522.jpeg")
    image_base64 = get_image_as_base64(image_path)

    apply_modern_styles()

    # Add Font Awesome icons and custom CSS
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .profile-section, .vision-section, .feature-card {
                text-align: center;
                padding: 2rem;
                background: rgba(45, 45, 45, 0.9);
                border-radius: 20px;
                margin: 2rem auto;
                max-width: 800px;
            }

            .profile-image {
                width: 200px;
                height: 200px;
                border-radius: 50%;
                margin: 0 auto 1.5rem;
                display: block;
                object-fit: cover;
                border: 4px solid #4CAF50;
            }

            .profile-name {
                font-size: 2.5rem;
                color: white;
                margin-bottom: 0.5rem;
            }

            .profile-title {
                font-size: 1.2rem;
                color: #4CAF50;
                margin-bottom: 1.5rem;
            }

            .social-links {
                display: flex;
                justify-content: center;
                gap: 1.5rem;
                margin: 2rem 0;
            }

            .social-link {
                font-size: 2rem;
                color: #4CAF50;
                transition: all 0.3s ease;
                padding: 0.5rem;
                border-radius: 50%;
                background: rgba(76, 175, 80, 0.1);
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                text-decoration: none;
            }

            .social-link:hover {
                transform: translateY(-5px);
                background: #4CAF50;
                color: white;
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
            }

            .bio-text {
                color: #ddd;
                line-height: 1.8;
                font-size: 1.1rem;
                margin-top: 2rem;
                text-align: left;
            }

            .vision-text {
                color: #ddd;
                line-height: 1.8;
                font-size: 1.1rem;
                font-style: italic;
                margin: 1.5rem 0;
                text-align: left;
            }

            .vision-icon {
                font-size: 2.5rem;
                color: #4CAF50;
                margin-bottom: 1rem;
            }

            .vision-title {
                font-size: 2rem;
                color: white;
                margin-bottom: 1rem;
            }

            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem;
                margin: 2rem auto;
                max-width: 1200px;
            }

            .feature-card {
                padding: 2rem;
                margin: 0;
            }

            .feature-icon {
                font-size: 2.5rem;
                color: #4CAF50;
                margin-bottom: 1rem;
            }

            .feature-title {
                font-size: 1.5rem;
                color: white;
                margin: 1rem 0;
            }

            .feature-description {
                color: #ddd;
                line-height: 1.6;
            }
        </style>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">About Resume Analyzer(AI)</h1>
            <p class="hero-subtitle">A powerful AI-driven platform for optimizing your resume</p>
        </div>
    """, unsafe_allow_html=True)

    # Profile Section
    st.markdown(f"""
        <div class="profile-section">
            <img src="{image_base64 if image_base64 else 'https://avatars.githubusercontent.com/latamishra5'}"
                 alt="Lata Mishra"
                 class="profile-image"
                 onerror="this.onerror=null; this.src='https://avatars.githubusercontent.com/latamishra5';">
            <h2 class="profile-name">Lata Mishra</h2>
            <p class="profile-title">Full Stack Web Developer</p>
            <div class="social-links">
                <a href="https://github.com/latamishra5" class="social-link" target="_blank">
                    <i class="fab fa-github"></i>
                </a>
                <a href="https://www.linkedin.com/in/latamishra5/" class="social-link" target="_blank">
                    <i class="fab fa-linkedin"></i>
                </a>
                <a href="mailto:latamishra987@gmail.com" class="social-link" target="_blank">
                    <i class="fas fa-envelope"></i>
                </a>
            </div>
            <p class="bio-text">
                Hello! I'm a passionate Full Stack Web Developer.
                I created Resume Analyzer(AI) to revolutionize how job seekers approach their career journey.
                With my background in both software development and AI, I've designed this platform to
                provide intelligent, data-driven insights for resume optimization.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Vision Section
    st.markdown("""
        <div class="vision-section">
            <i class="fas fa-lightbulb vision-icon"></i>
            <h2 class="vision-title">Our Vision</h2>
            <p class="vision-text">
                "Resume Analyzer(AI) represents my vision of democratizing career advancement through technology.
                By combining cutting-edge AI with intuitive design, this platform empowers job seekers at
                every career stage to showcase their true potential and stand out in today's competitive job market."
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Features Section
    st.markdown("""
        <div class="features-grid">
            <div class="feature-card">
                <i class="fas fa-robot feature-icon"></i>
                <h3 class="feature-title">AI-Powered Analysis</h3>
                <p class="feature-description">
                    Advanced AI algorithms provide detailed insights and suggestions to optimize your resume for maximum impact.
                </p>
            </div>
            <div class="feature-card">
                <i class="fas fa-chart-line feature-icon"></i>
                <h3 class="feature-title">Data-Driven Insights</h3>
                <p class="feature-description">
                    Make informed decisions with our analytics-based recommendations and industry insights.
                </p>
            </div>
            <div class="feature-card">
                <i class="fas fa-shield-alt feature-icon"></i>
                <h3 class="feature-title">Privacy First</h3>
                <p class="feature-description">
                    Your data security is our priority. We ensure your information is always protected and private.
                </p>
            </div>
        </div>
        <div style="text-align: center; margin: 3rem 0;">
            <a href="?page=analyzer" class="cta-button">
                Start Your Journey
                <i class="fas fa-arrow-right" style="margin-left: 10px;"></i>
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.toast("Check out these repositories: [Iriswise](https://github.com/latamishra5/Iriswise)", icon="ℹ️")
