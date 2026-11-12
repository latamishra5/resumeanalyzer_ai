"""Home page view."""

import streamlit as st

from frontend.components.ui_components import apply_modern_styles, feature_card


def render_home():
    apply_modern_styles()

    st.markdown(
        """
        <div class="page-header hero-header">
            <span class="hero-badge">AI-POWERED ATS &amp; CAREER PLATFORM</span>
            <h1 class="header-title">Optimize Every Resume Before You Apply</h1>
            <p class="header-subtitle">
                Benchmark your resume against role-specific ATS criteria, uncover keyword and impact gaps with AI,
                and generate clean, recruiter-ready resumes in minutes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta1, cta2, _ = st.columns([1.2, 1.2, 2.6])
    with cta1:
        if st.button(
            "Analyze My Resume",
            key="get_started_btn",
            help="Upload your resume for ATS & AI evaluation",
            type="primary",
            width="stretch",
        ):
            st.session_state.page = "resume_analyzer"
            st.rerun()
    with cta2:
        if st.button(
            "Open Resume Builder",
            key="home_open_builder_btn",
            help="Create a formatted DOCX resume from templates",
            width="stretch",
        ):
            st.session_state.page = "resume_builder"
            st.rerun()

    st.markdown("### Platform Capabilities")
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    feature_card(
        "fas fa-robot",
        "AI & JD Gap Analysis",
        "Evaluate resumes with Google Gemini AI (and deterministic ATS scoring fallback) tailored to your target role and job description.",
    )
    feature_card(
        "fas fa-check-double",
        "ATS Compatibility Audit",
        "Inspect section structure, keyword coverage, formatting hygiene, and export structured PDF audit reports.",
    )
    feature_card(
        "fas fa-file-alt",
        "Template Resume Builder",
        "Author experience, projects, skills, and education cleanly and export formatted Modern, Professional, Minimal, or Creative DOCX files.",
    )
    feature_card(
        "fas fa-chart-line",
        "Analytics & Job Discovery",
        "Track resume trends on the analytics dashboard and discover targeted job listings across leading portals.",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### How It Works")
    s1, s2, s3 = st.columns(3)
    steps = [
        ("1", "Upload or Build", "Upload a PDF or DOCX resume, or structure a new resume inside the guided builder."),
        ("2", "Run ATS & AI Review", "Select a target job role or paste a custom job description to identify missing keywords and impact improvements."),
        ("3", "Refine & Export", "Apply actionable edits and download a polished DOCX resume or PDF analysis report."),
    ]
    for col, (num, title, desc) in zip((s1, s2, s3), steps):
        with col:
            st.markdown(
                f"""
                <div class="step-card">
                    <div class="step-number">{num}</div>
                    <h4 style="margin: 0 0 0.4rem 0; color: #f8fafc;">{title}</h4>
                    <p style="margin: 0; color: #94a3b8; font-size: 0.92rem; line-height: 1.55;">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
