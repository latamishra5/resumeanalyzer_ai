"""Standard and AI Resume Analyzer page view."""

from datetime import datetime, timedelta
import html
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.analyzers.ai_resume_analyzer import AIResumeAnalyzer
from backend.config.courses import (
    COURSES_BY_CATEGORY,
    INTERVIEW_VIDEOS,
    RESUME_VIDEOS,
    get_category_for_role,
    get_courses_for_role,
)
from backend.database.connection import (
    get_detailed_ai_analysis_stats,
    save_ai_analysis_data,
    save_analysis_data,
    save_resume_data,
)
from frontend.components.ui_components import apply_modern_styles, page_header

logger = logging.getLogger(__name__)


def _st_notifier(level, message):
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "code":
        st.code(message)
    else:
        st.info(message)


def render_empty_state(icon, message):
    """Render an empty state with icon and message"""
    return f"""
        <div style='text-align: center; padding: 2rem; color: #666;'>
            <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
            <p style='margin: 0;'>{message}</p>
        </div>
    """


def render_analyzer(analyzer, ai_analyzer, job_roles):
    """Render the resume analyzer page"""
    apply_modern_styles()

    page_header(
        "Resume Analyzer",
        "Get instant AI-powered feedback to optimize your resume",
    )

    analyzer_tabs = st.tabs(["Standard Analyzer", "AI Analyzer"])

    with analyzer_tabs[0]:
        categories = list(job_roles.keys())
        selected_category = st.selectbox("Job Category", categories, key="standard_category")

        roles = list(job_roles[selected_category].keys())
        selected_role = st.selectbox("Specific Role", roles, key="standard_role")

        role_info = job_roles[selected_category][selected_role]

        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>{selected_role}</h3>
            <p>{role_info['description']}</p>
            <h4>Required Skills:</h4>
            <p>{', '.join(role_info['required_skills'])}</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload your resume",
            type=['pdf', 'docx'],
            key="standard_file",
        )

        if not uploaded_file:
            st.markdown(
                render_empty_state(
                    "fas fa-cloud-upload-alt",
                    "Upload your resume to get started with standard analysis",
                ),
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <style>
                .upload-button {
                    background: linear-gradient(90deg, #4b6cb7, #182848);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 15px 25px;
                    font-size: 18px;
                    font-weight: bold;
                    cursor: pointer;
                    width: 100%;
                    text-align: center;
                    margin: 20px 0;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;
                }
                .upload-button:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 6px 15px rgba(0,0,0,0.3);
                }
                </style>
                """, unsafe_allow_html=True)

        if uploaded_file:
            analyze_standard = st.button(
                "Analyze My Resume",
                icon=":material/manage_search:",
                type="primary",
                width="stretch",
                key="analyze_standard_button",
            )

            if analyze_standard:
                with st.spinner("Analyzing your document..."):
                    text = ""
                    try:
                        if uploaded_file.type == "application/pdf":
                            try:
                                text = analyzer.extract_text_from_pdf(uploaded_file)
                            except Exception as pdf_error:
                                st.error(f"PDF extraction failed: {str(pdf_error)}")
                                st.info("Trying alternative PDF extraction method...")
                                try:
                                    text = ai_analyzer.extract_text_from_pdf(uploaded_file)
                                except Exception as backup_error:
                                    st.error(f"All PDF extraction methods failed: {str(backup_error)}")
                                    return
                        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                            try:
                                text = analyzer.extract_text_from_docx(uploaded_file)
                            except Exception as docx_error:
                                st.error(f"DOCX extraction failed: {str(docx_error)}")
                                try:
                                    text = ai_analyzer.extract_text_from_docx(uploaded_file)
                                except Exception as backup_error:
                                    st.error(f"All DOCX extraction methods failed: {str(backup_error)}")
                                    return
                        else:
                            text = uploaded_file.getvalue().decode()

                        if not text or text.strip() == "":
                            st.error("Could not extract any text from the uploaded file. Please try a different file.")
                            return
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        return

                    analysis = analyzer.analyze_resume({'raw_text': text}, role_info)

                    if 'error' in analysis:
                        st.error(analysis['error'])
                        return

                    if analysis.get('document_type') != 'resume':
                        st.error(f"This appears to be a {analysis['document_type']} document, not a resume.")
                        st.warning("Please upload a proper resume for ATS analysis.")
                        return

                    resume_data = {
                        'personal_info': {
                            'full_name': analysis.get('name', ''),
                            'name': analysis.get('name', ''),
                            'email': analysis.get('email', ''),
                            'phone': analysis.get('phone', ''),
                            'linkedin': analysis.get('linkedin', ''),
                            'github': analysis.get('github', ''),
                            'portfolio': analysis.get('portfolio', ''),
                        },
                        'summary': analysis.get('summary', ''),
                        'target_role': selected_role,
                        'target_category': selected_category,
                        'education': analysis.get('education', []),
                        'experience': analysis.get('experience', []),
                        'projects': analysis.get('projects', []),
                        'skills': analysis.get('skills', []),
                        'template': '',
                    }

                    st.session_state["last_parsed_resume"] = resume_data
                    st.session_state["last_resume_skills"] = analysis.get("skills", [])
                    active_uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None

                    try:
                        resume_id = save_resume_data(resume_data, user_id=active_uid)
                        analysis_data = {
                            'resume_id': resume_id,
                            'ats_score': analysis['ats_score'],
                            'keyword_match_score': analysis['keyword_match']['score'],
                            'format_score': analysis['format_score'],
                            'section_score': analysis['section_score'],
                            'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                            'recommendations': ','.join(analysis['suggestions']),
                        }
                        save_analysis_data(resume_id, analysis_data)
                        st.success("Resume data saved successfully!")
                    except Exception as e:
                        logger.exception("Error saving standard analysis to database: %s", e)
                        st.error(f"Error saving to database: {str(e)}")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("""
                    <div class="feature-card">
                        <h2>ATS Score</h2>
                        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                            <div style="
                                position: absolute;
                                width: 150px;
                                height: 150px;
                                border-radius: 50%;
                                background: conic-gradient(
                                    #4CAF50 0% {score}%,
                                    #2c2c2c {score}% 100%
                                );
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            ">
                                <div style="
                                    width: 120px;
                                    height: 120px;
                                    background: #1a1a1a;
                                    border-radius: 50%;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: {color};
                                ">
                                    {score}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 10px;">
                            <span style="
                                font-size: 1.2em;
                                color: {color};
                                font-weight: bold;
                            ">
                                {status}
                            </span>
                        </div>
                    """.format(
                        score=analysis['ats_score'],
                        color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis['ats_score'] >= 60 else '#FF4444',
                        status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis['ats_score'] >= 60 else 'Needs Improvement',
                    ), unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("""
                    <div class="feature-card">
                        <h2>Skills Match</h2>
                    """, unsafe_allow_html=True)

                    st.metric("Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")

                    if analysis['keyword_match']['missing_skills']:
                        st.markdown("#### Missing Skills:")
                        for skill in analysis['keyword_match']['missing_skills']:
                            st.markdown(f"- {skill}")

                    st.markdown("</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Format Analysis</h2>
                    """, unsafe_allow_html=True)

                    st.metric("Format Score", f"{int(analysis.get('format_score', 0))}%")
                    st.metric("Section Score", f"{int(analysis.get('section_score', 0))}%")

                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("""
                    <div class="feature-card">
                        <h2><i class="fas fa-clipboard-list"></i> Resume Improvement Suggestions</h2>
                    """, unsafe_allow_html=True)

                    if analysis.get('contact_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-address-book"></i> Contact Information</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('contact_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    if analysis.get('summary_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-align-left"></i> Professional Summary</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('summary_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    if analysis.get('skills_suggestions') or analysis['keyword_match']['missing_skills']:
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-bullseye"></i> Skills</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('skills_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> Consider adding these relevant skills:</li>", unsafe_allow_html=True)
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    if analysis.get('experience_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-briefcase"></i> Work Experience</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('experience_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    if analysis.get('education_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-graduation-cap"></i> Education</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('education_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    if analysis.get('format_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'><i class="fas fa-file-alt"></i> Formatting</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('format_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'><i class='fas fa-check' style='color:#4CAF50;'></i> {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                    <div class="feature-card">
                        <h2><i class="fas fa-book"></i> Recommended Courses</h2>
                    """, unsafe_allow_html=True)

                courses = get_courses_for_role(selected_role)
                if not courses:
                    category = get_category_for_role(selected_role)
                    courses = COURSES_BY_CATEGORY.get(category, {}).get(selected_role, [])

                cols = st.columns(2)
                for i, course in enumerate(courses[:6]):
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h4>{course[0]}</h4>
                            <a href='{course[1]}' target='_blank'>View Course</a>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                    <div class="feature-card">
                        <h2><i class="fas fa-play-circle"></i> Helpful Videos</h2>
                    """, unsafe_allow_html=True)

                tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])

                with tab1:
                    for category, videos in RESUME_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])

                with tab2:
                    for category, videos in INTERVIEW_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])

                st.markdown("</div>", unsafe_allow_html=True)

    with analyzer_tabs[1]:
        st.markdown("""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>AI-Powered Resume Analysis</h3>
            <p>Get detailed insights from advanced AI models that analyze your resume and provide personalized recommendations.</p>
            <p><strong>Upload your resume to get AI-powered analysis and recommendations.</strong></p>
        </div>
        """, unsafe_allow_html=True)

        ai_model = st.selectbox(
            "Select AI Model",
            ["Google Gemini"],
            help="Choose the AI model to analyze your resume",
        )

        use_custom_job_desc = st.checkbox(
            "Use custom job description",
            value=False,
            help="Enable this to provide a specific job description for more targeted analysis",
        )

        custom_job_description = ""
        if use_custom_job_desc:
            custom_job_description = st.text_area(
                "Paste the job description here",
                height=200,
                placeholder="Paste the full job description from the company here for more targeted analysis...",
                help="Providing the actual job description will help the AI analyze your resume specifically for this position",
            )

            st.markdown("""
            <div style='background-color: #2e7d32; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                <p><i class="fas fa-lightbulb"></i> <strong>Pro Tip:</strong> Including the actual job description significantly improves the accuracy of the analysis and provides more relevant recommendations tailored to the specific position.</p>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("AI Analyzer Statistics", icon=":material/analytics:", expanded=False):
            try:
                ai_stats = get_detailed_ai_analysis_stats()

                if ai_stats["total_analyses"] > 0:
                    st.markdown("""
                    <style>
                    .stats-card {
                        background: linear-gradient(135deg, #1e3c72, #2a5298);
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 15px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }
                    .stats-value {
                        font-size: 28px;
                        font-weight: bold;
                        color: white;
                        margin: 10px 0;
                    }
                    .stats-label {
                        font-size: 14px;
                        color: rgba(255, 255, 255, 0.8);
                        text-transform: uppercase;
                        letter-spacing: 1px;
                    }
                    .score-card {
                        background: linear-gradient(135deg, #11998e, #38ef7d);
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 15px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="stats-card">
                            <div class="stats-label">Total AI Analyses</div>
                            <div class="stats-value">{ai_stats["total_analyses"]}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        score_color = "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats["average_score"] >= 60 else "#FF5252"
                        st.markdown(f"""
                        <div class="stats-card" style="background: linear-gradient(135deg, #2c3e50, {score_color});">
                            <div class="stats-label">Average Resume Score</div>
                            <div class="stats-value">{ai_stats["average_score"]}/100</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=ai_stats["average_score"],
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Score", 'font': {'size': 14, 'color': 'white'}},
                            gauge={
                                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                                'bar': {'color': "#38ef7d" if ai_stats["average_score"] >= 80 else "#FFEB3B" if ai_stats["average_score"] >= 60 else "#FF5252"},
                                'bgcolor': "rgba(0,0,0,0)",
                                'borderwidth': 2,
                                'bordercolor': "white",
                                'steps': [
                                    {'range': [0, 40], 'color': 'rgba(255, 82, 82, 0.3)'},
                                    {'range': [40, 70], 'color': 'rgba(255, 235, 59, 0.3)'},
                                    {'range': [70, 100], 'color': 'rgba(56, 239, 125, 0.3)'},
                                ],
                            },
                        ))

                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font={'color': "white"},
                            height=150,
                            margin=dict(l=10, r=10, t=30, b=10),
                        )

                        st.plotly_chart(fig, width="stretch")

                    if ai_stats["model_usage"]:
                        st.markdown("### :material/smart_toy: Model Usage")
                        model_data = pd.DataFrame(ai_stats["model_usage"])

                        fig = px.pie(
                            model_data,
                            values="count",
                            names="model",
                            color_discrete_sequence=px.colors.qualitative.Bold,
                            hole=0.4,
                        )

                        fig.update_traces(
                            textposition='inside',
                            textinfo='percent+label',
                            marker=dict(line=dict(color='#000000', width=1.5)),
                        )

                        fig.update_layout(
                            margin=dict(l=20, r=20, t=30, b=20),
                            height=300,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="#ffffff", size=14),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.1,
                                xanchor="center",
                                x=0.5,
                            ),
                            title={
                                'text': 'AI Model Distribution',
                                'y': 0.95,
                                'x': 0.5,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': {'size': 18, 'color': 'white'},
                            },
                        )

                        st.plotly_chart(fig, width="stretch")

                    if ai_stats["top_job_roles"]:
                        st.markdown("### :material/work: Top Job Roles")
                        roles_data = pd.DataFrame(ai_stats["top_job_roles"])

                        fig = px.bar(
                            roles_data,
                            x="role",
                            y="count",
                            color="count",
                            color_continuous_scale=px.colors.sequential.Viridis,
                            labels={"role": "Job Role", "count": "Number of Analyses"},
                        )

                        fig.update_traces(
                            marker_line_width=1.5,
                            marker_line_color="white",
                            opacity=0.9,
                        )

                        fig.update_layout(
                            margin=dict(l=20, r=20, t=50, b=30),
                            height=350,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="#ffffff", size=14),
                            title={
                                'text': 'Most Analyzed Job Roles',
                                'y': 0.95,
                                'x': 0.5,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': {'size': 18, 'color': 'white'},
                            },
                            xaxis=dict(title="", tickangle=-45, tickfont=dict(size=12)),
                            yaxis=dict(title="Number of Analyses", gridcolor="rgba(255, 255, 255, 0.1)"),
                            coloraxis_showscale=False,
                        )

                        st.plotly_chart(fig, width="stretch")

                        st.markdown("### :material/trending_up: Analysis Trend")

                        today = datetime.now()
                        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
                        daily_counts = {
                            item["date"]: item["count"]
                            for item in ai_stats.get("daily_trend", [])
                        }
                        values = [daily_counts.get(d, 0) for d in dates]

                        trend_data = pd.DataFrame({'Date': dates, 'Analyses': values})

                        fig = px.line(
                            trend_data,
                            x='Date',
                            y='Analyses',
                            markers=True,
                            line_shape='spline',
                            color_discrete_sequence=["#38ef7d"],
                        )

                        fig.update_traces(
                            line=dict(width=3),
                            marker=dict(size=8, line=dict(width=2, color='white')),
                        )

                        fig.update_layout(
                            margin=dict(l=20, r=20, t=50, b=30),
                            height=300,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="#ffffff", size=14),
                            title={
                                'text': 'Analysis Activity (Last 7 Days)',
                                'y': 0.95,
                                'x': 0.5,
                                'xanchor': 'center',
                                'yanchor': 'top',
                                'font': {'size': 18, 'color': 'white'},
                            },
                            xaxis=dict(title="", gridcolor="rgba(255, 255, 255, 0.1)"),
                            yaxis=dict(title="Number of Analyses", gridcolor="rgba(255, 255, 255, 0.1)"),
                        )

                        st.plotly_chart(fig, width="stretch")

                    if ai_stats["score_distribution"]:
                        st.markdown("""
                        <h3 style='text-align: center; margin-bottom: 20px; background: linear-gradient(90deg, #4b6cb7, #182848); padding: 15px; border-radius: 10px; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);'>
                            <i class="fas fa-chart-bar"></i> Score Distribution Analysis
                        </h3>
                        """, unsafe_allow_html=True)

                        score_data = pd.DataFrame(ai_stats["score_distribution"])

                        fig = px.bar(
                            score_data,
                            x="range",
                            y="count",
                            color="range",
                            color_discrete_map={
                                "0-20": "#FF5252",
                                "21-40": "#FF7043",
                                "41-60": "#FFEB3B",
                                "61-80": "#8BC34A",
                                "81-100": "#38ef7d",
                            },
                            labels={"range": "Score Range", "count": "Number of Resumes"},
                            text="count",
                        )

                        fig.update_traces(
                            marker_line_width=2,
                            marker_line_color="white",
                            opacity=0.9,
                            textposition='outside',
                            textfont=dict(color="white", size=14, family="Arial, sans-serif"),
                            hovertemplate="<b>Score Range:</b> %{x}<br><b>Number of Resumes:</b> %{y}<extra></extra>",
                        )

                        fig.update_layout(
                            margin=dict(l=20, r=20, t=50, b=30),
                            height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="#ffffff", size=14, family="Arial, sans-serif"),
                            xaxis=dict(
                                title=dict(text="Score Range", font=dict(size=16, color="white")),
                                categoryorder="array",
                                categoryarray=["0-20", "21-40", "41-60", "61-80", "81-100"],
                                tickfont=dict(size=14, color="white"),
                                gridcolor="rgba(255, 255, 255, 0.1)",
                            ),
                            yaxis=dict(
                                title=dict(text="Number of Resumes", font=dict(size=16, color="white")),
                                tickfont=dict(size=14, color="white"),
                                gridcolor="rgba(255, 255, 255, 0.1)",
                                zeroline=False,
                            ),
                            showlegend=False,
                            bargap=0.2,
                            shapes=[
                                dict(
                                    type="rect",
                                    xref="paper",
                                    yref="paper",
                                    x0=0,
                                    y0=0,
                                    x1=1,
                                    y1=1,
                                    fillcolor="rgba(26, 26, 44, 0.5)",
                                    layer="below",
                                    line_width=0,
                                )
                            ],
                        )

                        if len(score_data) > 0:
                            max_count_idx = score_data["count"].idxmax()
                            max_range = score_data.iloc[max_count_idx]["range"]

                            fig.add_annotation(
                                x=0.5,
                                y=1.12,
                                xref="paper",
                                yref="paper",
                                text=f"Most resumes fall in the {max_range} score range",
                                showarrow=False,
                                font=dict(size=14, color="#FFEB3B"),
                                bgcolor="rgba(0,0,0,0.5)",
                                bordercolor="#FFEB3B",
                                borderwidth=1,
                                borderpad=4,
                                opacity=0.8,
                            )

                        st.markdown("""
                        <div style='background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 15px; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
                        """, unsafe_allow_html=True)

                        st.plotly_chart(fig, width="stretch")

                        st.markdown("""
                        <p style='color: white; text-align: center; font-style: italic; margin-top: 10px;'>
                            This chart shows the distribution of resume scores across different ranges, helping identify common performance levels.
                        </p>
                        </div>
                        """, unsafe_allow_html=True)

                    if ai_stats["recent_analyses"]:
                        st.markdown("""
                        <h3 style='text-align: center; margin-bottom: 20px; background: linear-gradient(90deg, #4b6cb7, #182848); padding: 15px; border-radius: 10px; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.2);'>
                            <i class="fas fa-clock"></i> Recent Resume Analyses
                        </h3>
                        """, unsafe_allow_html=True)

                        st.markdown("""
                        <style>
                        .modern-analyses-table {
                            width: 100%;
                            border-collapse: separate;
                            border-spacing: 0 8px;
                            margin-bottom: 20px;
                            font-family: 'Arial', sans-serif;
                        }
                        .modern-analyses-table th {
                            background: linear-gradient(135deg, #1e3c72, #2a5298);
                            color: white;
                            padding: 15px;
                            text-align: left;
                            font-weight: bold;
                            font-size: 14px;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                            border-radius: 8px;
                        }
                        .modern-analyses-table td {
                            padding: 15px;
                            background-color: rgba(30, 30, 30, 0.7);
                            border-top: 1px solid rgba(255, 255, 255, 0.05);
                            border-bottom: 1px solid rgba(0, 0, 0, 0.2);
                            color: white;
                        }
                        .modern-analyses-table tr td:first-child {
                            border-top-left-radius: 8px;
                            border-bottom-left-radius: 8px;
                        }
                        .modern-analyses-table tr td:last-child {
                            border-top-right-radius: 8px;
                            border-bottom-right-radius: 8px;
                        }
                        .modern-analyses-table tr:hover td {
                            background-color: rgba(60, 60, 60, 0.7);
                            transform: translateY(-2px);
                            transition: all 0.2s ease;
                            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                        }
                        .model-badge {
                            display: inline-block;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-weight: bold;
                            text-align: center;
                            font-size: 12px;
                            letter-spacing: 0.5px;
                            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        }
                        .model-gemini {
                            background: linear-gradient(135deg, #4e54c8, #8f94fb);
                            color: white;
                        }
                        .model-claude {
                            background: linear-gradient(135deg, #834d9b, #d04ed6);
                            color: white;
                        }
                        .score-pill {
                            display: inline-block;
                            padding: 8px 15px;
                            border-radius: 20px;
                            font-weight: bold;
                            text-align: center;
                            min-width: 70px;
                            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                        }
                        .score-high {
                            background: linear-gradient(135deg, #11998e, #38ef7d);
                            color: white;
                        }
                        .score-medium {
                            background: linear-gradient(135deg, #f2994a, #f2c94c);
                            color: white;
                        }
                        .score-low {
                            background: linear-gradient(135deg, #cb2d3e, #ef473a);
                            color: white;
                        }
                        .date-badge {
                            display: inline-block;
                            padding: 6px 12px;
                            border-radius: 20px;
                            background-color: rgba(255, 255, 255, 0.1);
                            color: #e0e0e0;
                            font-size: 12px;
                        }
                        .role-badge {
                            display: inline-block;
                            padding: 6px 12px;
                            border-radius: 8px;
                            background-color: rgba(33, 150, 243, 0.2);
                            color: #90caf9;
                            font-size: 13px;
                            max-width: 200px;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        }
                        </style>

                        <div style='background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 15px; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
                        <table class="modern-analyses-table">
                            <tr>
                                <th>AI Model</th>
                                <th>Score</th>
                                <th>Job Role</th>
                                <th>Date</th>
                            </tr>
                        """, unsafe_allow_html=True)

                        for analysis in ai_stats["recent_analyses"]:
                            score = analysis["score"]
                            score_class = "score-high" if score >= 80 else "score-medium" if score >= 60 else "score-low"

                            model_name = analysis["model"]
                            model_class = "model-gemini" if "Gemini" in model_name else "model-claude" if "Claude" in model_name else ""

                            try:
                                date_obj = datetime.strptime(analysis["date"], "%Y-%m-%d %H:%M:%S")
                                formatted_date = date_obj.strftime("%b %d, %Y")
                            except Exception:
                                formatted_date = analysis["date"]

                            st.markdown(f"""
                            <tr>
                                <td><div class="model-badge {model_class}">{html.escape(str(model_name))}</div></td>
                                <td><div class="score-pill {score_class}">{score}/100</div></td>
                                <td><div class="role-badge">{html.escape(str(analysis["job_role"]))}</div></td>
                                <td><div class="date-badge">{html.escape(str(formatted_date))}</div></td>
                            </tr>
                            """, unsafe_allow_html=True)

                        st.markdown("""
                        </table>

                        <p style='color: white; text-align: center; font-style: italic; margin-top: 15px;'>
                            These are the most recent resume analyses performed by our AI models.
                        </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No AI analysis data available yet. Upload and analyze resumes to see statistics here.")
            except Exception as e:
                st.error(f"Error loading AI analysis statistics: {str(e)}")

        categories = list(job_roles.keys())
        selected_category = st.selectbox("Job Category", categories, key="ai_category")

        roles = list(job_roles[selected_category].keys())
        selected_role = st.selectbox("Specific Role", roles, key="ai_role")

        role_info = job_roles[selected_category][selected_role]

        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>{selected_role}</h3>
            <p>{role_info['description']}</p>
            <h4>Required Skills:</h4>
            <p>{', '.join(role_info['required_skills'])}</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'], key="ai_file")

        if not uploaded_file:
            st.markdown(
                render_empty_state(
                    "fas fa-robot",
                    "Upload your resume to get AI-powered analysis and recommendations",
                ),
                unsafe_allow_html=True,
            )
        else:
            analyze_ai = st.button(
                "Analyze with AI",
                icon=":material/smart_toy:",
                type="primary",
                width="stretch",
                key="analyze_ai_button",
            )

            if analyze_ai:
                with st.spinner(f"Analyzing your resume with {ai_model}..."):
                    try:
                        if uploaded_file.type == "application/pdf":
                            _text = analyzer.extract_text_from_pdf(uploaded_file)
                        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                            _text = analyzer.extract_text_from_docx(uploaded_file)
                        else:
                            _text = uploaded_file.getvalue().decode()
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        st.stop()

                    try:
                        with st.spinner("AI is analyzing your resume..."):
                            progress_bar = st.progress(0)
                            selected_model = "Google Gemini"
                            progress_bar.progress(10)

                            local_ai_analyzer = AIResumeAnalyzer(notifier=_st_notifier)
                            if uploaded_file.type == "application/pdf":
                                resume_text = local_ai_analyzer.extract_text_from_pdf(uploaded_file)
                            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                resume_text = local_ai_analyzer.extract_text_from_docx(uploaded_file)
                            else:
                                resume_text = uploaded_file.getvalue().decode('utf-8')

                            progress_bar.progress(30)
                            job_role = selected_role if selected_role else "Not specified"
                            progress_bar.progress(50)

                            if use_custom_job_desc and custom_job_description:
                                analysis_result = local_ai_analyzer.analyze_resume_with_gemini(
                                    resume_text,
                                    job_role=job_role,
                                    job_description=custom_job_description,
                                )
                                st.session_state['used_custom_job_desc'] = True
                            else:
                                analysis_result = local_ai_analyzer.analyze_resume_with_gemini(
                                    resume_text,
                                    job_role=job_role,
                                )
                                st.session_state['used_custom_job_desc'] = False

                            progress_bar.progress(80)

                            if analysis_result and "error" not in analysis_result:
                                resume_score = analysis_result.get("resume_score", 0)
                                active_uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
                                save_ai_analysis_data(
                                    None,
                                    {
                                        "model_used": selected_model,
                                        "resume_score": resume_score,
                                        "job_role": job_role,
                                    },
                                    user_id=active_uid,
                                )

                            progress_bar.progress(100)

                            if analysis_result and "error" not in analysis_result:
                                if analysis_result.get("fallback_used") or analysis_result.get("analysis_mode") == "deterministic_fallback":
                                    st.info("Analyzed using deterministic local ATS heuristics (configure `GOOGLE_API_KEY` or `OPENROUTER_API_KEY` for live LLM review).")
                                else:
                                    st.success("Analysis complete.")

                                full_response = analysis_result.get("analysis", "")
                                resume_score = analysis_result.get("resume_score", 0)
                                ats_score = analysis_result.get("ats_score", 0)
                                model_used = analysis_result.get("model_used", selected_model)

                                st.session_state['full_analysis'] = full_response
                                st.session_state['last_ai_resume_text'] = resume_text
                                st.session_state['last_ai_structured'] = analysis_result.get("structured") or {}
                                st.session_state['last_ai_job_role'] = job_role
                                st.session_state['last_ai_job_desc'] = custom_job_description if st.session_state.get('used_custom_job_desc') else ""

                                st.markdown("## Full Analysis Report")
                                current_date = datetime.now().strftime("%B %d, %Y")

                                st.markdown(f"""
                                <div style="background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                    <h2 style="color: #ffffff; margin-bottom: 10px;">AI Resume Analysis Report</h2>
                                    <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                        <div style="flex: 1; min-width: 200px;">
                                            <p style="color: #ffffff;"><strong>Job Role:</strong> {html.escape(str(job_role)) if job_role else "Not specified"}</p>
                                            <p style="color: #ffffff;"><strong>Analysis Date:</strong> {current_date}</p>
                                        </div>
                                        <div style="flex: 1; min-width: 200px;">
                                            <p style="color: #ffffff;"><strong>AI Model:</strong> {html.escape(str(model_used))}</p>
                                            <p style="color: #ffffff;"><strong>Overall Score:</strong> {resume_score}/100 - {"Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"}</p>
                                            {f'<p style="color: #4CAF50;"><strong><i class="fas fa-check-circle"></i> Custom Job Description Used</strong></p>' if st.session_state.get('used_custom_job_desc', False) else ''}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                                col1, col2 = st.columns(2)

                                with col1:
                                    fig1 = go.Figure(go.Indicator(
                                        mode="gauge+number",
                                        value=resume_score,
                                        domain={'x': [0, 1], 'y': [0, 1]},
                                        title={'text': "Resume Score", 'font': {'size': 16}},
                                        gauge={
                                            'axis': {'range': [0, 100], 'tickwidth': 1},
                                            'bar': {'color': "#4CAF50" if resume_score >= 80 else "#FFA500" if resume_score >= 60 else "#FF4444"},
                                            'bgcolor': "white",
                                            'borderwidth': 2,
                                            'bordercolor': "gray",
                                            'steps': [
                                                {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'},
                                            ],
                                            'threshold': {
                                                'line': {'color': "red", 'width': 4},
                                                'thickness': 0.75,
                                                'value': 60,
                                            },
                                        },
                                    ))

                                    fig1.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                                    st.plotly_chart(fig1, width="stretch")

                                    status = "Excellent" if resume_score >= 80 else "Good" if resume_score >= 60 else "Needs Improvement"
                                    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)

                                with col2:
                                    fig2 = go.Figure(go.Indicator(
                                        mode="gauge+number",
                                        value=ats_score,
                                        domain={'x': [0, 1], 'y': [0, 1]},
                                        title={'text': "ATS Optimization Score", 'font': {'size': 16}},
                                        gauge={
                                            'axis': {'range': [0, 100], 'tickwidth': 1},
                                            'bar': {'color': "#4CAF50" if ats_score >= 80 else "#FFA500" if ats_score >= 60 else "#FF4444"},
                                            'bgcolor': "white",
                                            'borderwidth': 2,
                                            'bordercolor': "gray",
                                            'steps': [
                                                {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'},
                                            ],
                                            'threshold': {
                                                'line': {'color': "red", 'width': 4},
                                                'thickness': 0.75,
                                                'value': 60,
                                            },
                                        },
                                    ))

                                    fig2.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                                    st.plotly_chart(fig2, width="stretch")

                                    status = "Excellent" if ats_score >= 80 else "Good" if ats_score >= 60 else "Needs Improvement"
                                    st.markdown(f"<div style='text-align: center; font-weight: bold;'>{status}</div>", unsafe_allow_html=True)

                                if st.session_state.get('used_custom_job_desc', False) and custom_job_description:
                                    job_match_score = analysis_result.get("job_match_score", 0)
                                    if not job_match_score and "job_match" in analysis_result:
                                        job_match_score = analysis_result["job_match"].get("score", 0)

                                    if job_match_score:
                                        st.markdown("""
                                        <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px; margin-top: 20px;">
                                            <i class="fas fa-handshake"></i> Job Description Match Analysis
                                        </h3>
                                        """, unsafe_allow_html=True)

                                        col1, col2 = st.columns(2)

                                        with col1:
                                            fig3 = go.Figure(go.Indicator(
                                                mode="gauge+number",
                                                value=job_match_score,
                                                domain={'x': [0, 1], 'y': [0, 1]},
                                                title={'text': "Job Match Score", 'font': {'size': 16}},
                                                gauge={
                                                    'axis': {'range': [0, 100], 'tickwidth': 1},
                                                    'bar': {'color': "#4CAF50" if job_match_score >= 80 else "#FFA500" if job_match_score >= 60 else "#FF4444"},
                                                    'bgcolor': "white",
                                                    'borderwidth': 2,
                                                    'bordercolor': "gray",
                                                    'steps': [
                                                        {'range': [0, 40], 'color': 'rgba(255, 68, 68, 0.2)'},
                                                        {'range': [40, 60], 'color': 'rgba(255, 165, 0, 0.2)'},
                                                        {'range': [60, 80], 'color': 'rgba(255, 214, 0, 0.2)'},
                                                        {'range': [80, 100], 'color': 'rgba(76, 175, 80, 0.2)'},
                                                    ],
                                                    'threshold': {
                                                        'line': {'color': "red", 'width': 4},
                                                        'thickness': 0.75,
                                                        'value': 60,
                                                    },
                                                },
                                            ))

                                            fig3.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
                                            st.plotly_chart(fig3, width="stretch")

                                            match_status = "Excellent Match" if job_match_score >= 80 else "Good Match" if job_match_score >= 60 else "Low Match"
                                            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{match_status}</div>", unsafe_allow_html=True)

                                        with col2:
                                            st.markdown("""
                                            <div style="background-color: #262730; padding: 20px; border-radius: 10px; height: 100%;">
                                                <h4 style="color: #ffffff; margin-bottom: 15px;">What This Means</h4>
                                                <p style="color: #ffffff;">This score represents how well your resume matches the specific job description you provided.</p>
                                                <ul style="color: #ffffff; padding-left: 20px;">
                                                    <li><strong>80-100:</strong> Excellent match - your resume is highly aligned with this job</li>
                                                    <li><strong>60-79:</strong> Good match - your resume matches many requirements</li>
                                                    <li><strong>Below 60:</strong> Consider tailoring your resume more specifically to this job</li>
                                                </ul>
                                            </div>
                                            """, unsafe_allow_html=True)

                                structured = analysis_result.get("structured") or {}
                                if structured:
                                    st.markdown("### :material/fact_check: Structured ATS Gap Matrix")
                                    sec_scores = structured.get("section_scores", {})
                                    if sec_scores:
                                        sec_cols = st.columns(len(sec_scores))
                                        for idx, (sec_name, sec_val) in enumerate(sec_scores.items()):
                                            with sec_cols[idx]:
                                                st.metric(sec_name, f"{sec_val}%")

                                    matched_kw = structured.get("matched_keywords", [])
                                    missing_kw = structured.get("missing_keywords", [])
                                    kw_col1, kw_col2 = st.columns(2)
                                    with kw_col1:
                                        matched_pills = " ".join(
                                            f"<span style='display:inline-block;margin:3px;padding:4px 10px;border-radius:999px;background:rgba(16,185,129,0.18);color:#34d399;border:1px solid rgba(16,185,129,0.4);font-size:0.85rem;'>{html.escape(str(k), quote=True)}</span>"
                                            for k in matched_kw
                                        ) or "<span style='color:#94a3b8;'>No target keywords detected yet</span>"
                                        st.markdown(
                                            f"<div style='background:#1e293b;padding:14px;border-radius:10px;'><strong><i class='fas fa-check-circle' style='color:#34d399;'></i> Matched Keywords ({len(matched_kw)})</strong><div style='margin-top:8px;'>{matched_pills}</div></div>",
                                            unsafe_allow_html=True,
                                        )
                                    with kw_col2:
                                        missing_pills = " ".join(
                                            f"<span style='display:inline-block;margin:3px;padding:4px 10px;border-radius:999px;background:rgba(245,158,11,0.18);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);font-size:0.85rem;'>{html.escape(str(k), quote=True)}</span>"
                                            for k in missing_kw
                                        ) or "<span style='color:#34d399;'>Strong coverage across all detected keywords</span>"
                                        st.markdown(
                                            f"<div style='background:#1e293b;padding:14px;border-radius:10px;'><strong><i class='fas fa-exclamation-triangle' style='color:#fbbf24;'></i> Missing / Priority Keywords ({len(missing_kw)})</strong><div style='margin-top:8px;'>{missing_pills}</div></div>",
                                            unsafe_allow_html=True,
                                        )

                                    suggested_rewrites = structured.get("bullet_rewrites", [])
                                    if suggested_rewrites:
                                        st.markdown("### :material/auto_fix_high: Suggested Bullet Upgrades")
                                        for rw in suggested_rewrites:
                                            orig_esc = html.escape(str(rw.get("original", "")), quote=True)
                                            imp_esc = html.escape(str(rw.get("improved", "")), quote=True)
                                            reason_esc = html.escape(str(rw.get("reason", "")), quote=True)
                                            st.markdown(
                                                f"""
                                                <div style="background:#1e293b;padding:12px 14px;border-radius:8px;margin-bottom:8px;border-left:4px solid #38bdf8;">
                                                    <div style="color:#94a3b8;font-size:0.85rem;"><strong>Original:</strong> {orig_esc}</div>
                                                    <div style="color:#e2e8f0;margin-top:4px;"><strong>Improved:</strong> {imp_esc}</div>
                                                    <div style="color:#38bdf8;font-size:0.8rem;margin-top:4px;">{reason_esc}</div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )

                                formatted_analysis = html.escape(full_response)

                                section_styles = {
                                    "## Overall Assessment": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-chart-line"></i> Overall Assessment
                                        </h3>
                                        <div class="section-content">""",
                                    "## Professional Profile Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #047857, #10b981); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-user-tie"></i> Professional Profile Analysis
                                        </h3>
                                        <div class="section-content">""",
                                    "## Skills Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #4f46e5, #818cf8); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-tools"></i> Skills Analysis
                                        </h3>
                                        <div class="section-content">""",
                                    "## Experience Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #9f1239, #e11d48); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-briefcase"></i> Experience Analysis
                                        </h3>
                                        <div class="section-content">""",
                                    "## Education Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #854d0e, #eab308); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-graduation-cap"></i> Education Analysis
                                        </h3>
                                        <div class="section-content">""",
                                    "## Key Strengths": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #166534, #22c55e); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-check-circle"></i> Key Strengths
                                        </h3>
                                        <div class="section-content">""",
                                    "## Areas for Improvement": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #9f1239, #fb7185); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-exclamation-circle"></i> Areas for Improvement
                                        </h3>
                                        <div class="section-content">""",
                                    "## ATS Optimization Assessment": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #0e7490, #06b6d4); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-robot"></i> ATS Optimization Assessment
                                        </h3>
                                        <div class="section-content">""",
                                    "## Recommended Courses": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #5b21b6, #8b5cf6); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-book"></i> Recommended Courses
                                        </h3>
                                        <div class="section-content">""",
                                    "## Resume Score": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #0369a1, #0ea5e9); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-star"></i> Resume Score
                                        </h3>
                                        <div class="section-content">""",
                                    "## Role Alignment Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #7c2d12, #ea580c); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-bullseye"></i> Role Alignment Analysis
                                        </h3>
                                        <div class="section-content">""",
                                    "## Job Match Analysis": """<div class="report-section">
                                        <h3 style="background: linear-gradient(90deg, #4d7c0f, #84cc16); color: white; padding: 10px; border-radius: 5px;">
                                            <i class="fas fa-handshake"></i> Job Match Analysis
                                        </h3>
                                        <div class="section-content">""",
                                }

                                for section, style in section_styles.items():
                                    if section in formatted_analysis:
                                        formatted_analysis = formatted_analysis.replace(section, style)
                                        next_section = False
                                        for next_sec in section_styles.keys():
                                            if next_sec != section and next_sec in formatted_analysis.split(style)[1]:
                                                split_text = formatted_analysis.split(style)[1].split(next_sec)
                                                formatted_analysis = (
                                                    formatted_analysis.split(style)[0]
                                                    + style
                                                    + split_text[0]
                                                    + "</div></div>"
                                                    + next_sec
                                                    + "".join(split_text[1:])
                                                )
                                                next_section = True
                                                break
                                        if not next_section:
                                            formatted_analysis = formatted_analysis + "</div></div>"

                                formatted_analysis = formatted_analysis.replace("</div></div></div></div>", "</div></div>")

                                if formatted_analysis.endswith("</div>"):
                                    open_tags = formatted_analysis.count("<div")
                                    close_tags = formatted_analysis.count("</div>")
                                    if close_tags > open_tags:
                                        excess = close_tags - open_tags
                                        formatted_analysis = formatted_analysis[:-6 * excess]

                                formatted_analysis = formatted_analysis.replace("&lt;/div&gt;", "")
                                formatted_analysis = formatted_analysis.replace("&lt;div&gt;", "")

                                st.markdown("""
                                <style>
                                    .report-section {
                                        margin-bottom: 25px;
                                        border: 1px solid #4B4B4B;
                                        border-radius: 8px;
                                        overflow: hidden;
                                    }
                                    .section-content {
                                        padding: 15px;
                                        background-color: #262730;
                                        color: #ffffff;
                                    }
                                    .report-section h3 {
                                        margin-top: 0;
                                        font-weight: 600;
                                    }
                                    .report-section ul {
                                        padding-left: 20px;
                                    }
                                    .report-section p {
                                        color: #ffffff;
                                        margin-bottom: 10px;
                                    }
                                    .report-section li {
                                        color: #ffffff;
                                        margin-bottom: 5px;
                                    }
                                </style>
                                """, unsafe_allow_html=True)

                                st.markdown(f"""
                                <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4B4B4B; color: #ffffff;">
                                    {formatted_analysis}
                                </div>
                                """, unsafe_allow_html=True)

                                pdf_buffer = local_ai_analyzer.generate_pdf_report(
                                    analysis_result={
                                        "score": resume_score,
                                        "ats_score": ats_score,
                                        "model_used": model_used,
                                        "full_response": full_response,
                                        "strengths": analysis_result.get("strengths", []),
                                        "weaknesses": analysis_result.get("weaknesses", []),
                                        "used_custom_job_desc": st.session_state.get('used_custom_job_desc', False),
                                        "custom_job_description": custom_job_description if st.session_state.get('used_custom_job_desc', False) else "",
                                    },
                                    candidate_name=st.session_state.get('candidate_name', 'Candidate'),
                                    job_role=selected_role,
                                )

                                if pdf_buffer:
                                    st.download_button(
                                        label="Download PDF Report",
                                        icon=":material/download:",
                                        data=pdf_buffer,
                                        file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                        mime="application/pdf",
                                        width="stretch",
                                    )
                                else:
                                    st.error("PDF generation failed. Please try again later.")
                            else:
                                st.error(f"Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                    except Exception as ai_error:
                        logger.exception("Error during AI analysis: %s", ai_error)
                        st.error(f"Error during AI analysis: {str(ai_error)}")

            st.markdown("---")
            with st.expander(":material/auto_fix_high: AI Bullet Point Rewriter (STAR Optimizer)"):
                st.caption("Paste 1 to 6 experience bullets to strengthen action verbs and measurable impact phrasing.")
                bullet_input = st.text_area(
                    "Bullet points to rewrite (one per line)",
                    placeholder="- Worked on backend API endpoints for user dashboard\n- Responsible for testing database migrations",
                    height=120,
                    key="ai_bullet_rewrite_input",
                )
                if st.button("Rewrite Bullets", icon=":material/auto_fix_high:", key="run_bullet_rewrite_btn"):
                    if not bullet_input.strip():
                        st.warning("Enter at least one bullet point to rewrite.")
                    else:
                        rewriter = AIResumeAnalyzer(notifier=_st_notifier)
                        rewrites = rewriter.rewrite_resume_bullets(
                            bullet_input,
                            job_role=st.session_state.get("last_ai_job_role") or selected_role,
                            job_description=custom_job_description if use_custom_job_desc else None,
                        )
                        if rewrites:
                            for idx, rw in enumerate(rewrites, 1):
                                st.markdown(f"**Bullet {idx}**")
                                st.caption(f"Original: {rw.get('original', '')}")
                                st.success(rw.get("improved", ""))
                                st.caption(f"Why it improves ATS impact: {rw.get('reason', '')}")
                        else:
                            st.info("Could not parse bullet points. Add one bullet per line.")
