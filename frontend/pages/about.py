"""Product overview, architecture, and privacy/security page."""

import streamlit as st

from frontend.components.ui_components import apply_modern_styles


def render_about():
    """Render the product overview and security architecture page."""
    apply_modern_styles()

    st.markdown(
        """
        <div class="hero-section">
            <span class="hero-badge">PLATFORM OVERVIEW &amp; TRUST</span>
            <h1 class="hero-title">About Resume Analyzer(AI)</h1>
            <p class="hero-subtitle">
                A modular ATS diagnostics, AI resume evaluation, and structured resume authoring platform built for modern hiring workflows.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="features-grid">
            <div class="feature-card">
                <i class="fas fa-cogs feature-icon"></i>
                <h3 class="feature-title">Hybrid ATS + AI Engine</h3>
                <p class="feature-description">
                    Combines deterministic ATS section/keyword verification with Google Gemini AI evaluation and custom job-description matching.
                </p>
            </div>
            <div class="feature-card">
                <i class="fas fa-shield-alt feature-icon"></i>
                <h3 class="feature-title">Security &amp; Role Separation</h3>
                <p class="feature-description">
                    Public workflows are strictly isolated from administrative operations, with salted scrypt password hashing and SQLAlchemy parameterized queries.
                </p>
            </div>
            <div class="feature-card">
                <i class="fas fa-server feature-icon"></i>
                <h3 class="feature-title">Cloud-Ready Architecture</h3>
                <p class="feature-description">
                    Supports local SQLite for single-node setups and managed PostgreSQL (<code>DATABASE_URL</code>) inside containerized cloud deployments.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Technical Architecture & Data Handling")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="card">
                <h4 style="margin-top: 0; color: #f8fafc;">Supported Analysis Pipeline</h4>
                <ul style="color: #94a3b8; line-height: 1.7; padding-left: 1.2rem; margin-bottom: 0;">
                    <li><strong>Document Parsing:</strong> Text extraction for PDF and DOCX resumes with automatic resume vs. non-resume validation.</li>
                    <li><strong>Standard ATS Audit:</strong> Checks contact completeness, section structure, formatting hygiene, and required role skills.</li>
                    <li><strong>AI Deep Review:</strong> Google Gemini evaluation with deterministic heuristic fallback when offline or unconfigured.</li>
                    <li><strong>PDF Reporting:</strong> Downloadable structured analysis reports powered by ReportLab.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="card">
                <h4 style="margin-top: 0; color: #f8fafc;">Privacy &amp; Administration</h4>
                <ul style="color: #94a3b8; line-height: 1.7; padding-left: 1.2rem; margin-bottom: 0;">
                    <li><strong>No Frontend Admin Surface:</strong> Admin authentication, record exports, and audit logs live strictly in the isolated backend console.</li>
                    <li><strong>Clean Output Escaping:</strong> Dynamic user content and job listings are HTML-escaped and URL-validated before rendering.</li>
                    <li><strong>Environment Secrets:</strong> API keys and admin credentials are read from environment variables or <code>.env</code>, never hardcoded.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="text-align: center; margin: 2rem 0 1rem 0;">
            <a href="?page=analyzer" class="cta-button">
                Launch Resume Analyzer &rarr;
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
