"""
Resume Analyzer(AI) - Frontend Application Coordinator
"""

from datetime import datetime
from pathlib import Path
import sys

# Ensure project root is importable if launched directly via `streamlit run frontend/app.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import requests
import streamlit as st

from backend.analyzers.ai_resume_analyzer import AIResumeAnalyzer
from backend.analyzers.resume_analyzer import ResumeAnalyzer
from backend.builders.resume_builder import ResumeBuilder
from backend.config.job_roles import JOB_ROLES
from backend.config.settings import STYLE_CSS_PATH
from backend.database.connection import init_database, log_admin_action, verify_admin
from frontend.pages.about import render_about
from frontend.pages.analyzer import _st_notifier, render_analyzer, render_empty_state
from frontend.pages.builder import render_builder
from frontend.pages.dashboard import DashboardManager, render_dashboard
from frontend.pages.feedback import render_feedback_page
from frontend.pages.home import render_home
from frontend.pages.job_search import render_job_search_page


def configure_page():
    """Configure Streamlit page settings (must run before any other st.* call)."""
    st.set_page_config(
        page_title="Resume Analyzer(AI)",
        page_icon="🚀",
        layout="wide",
    )


class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': '',
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': [],
                },
            }

        # Initialize navigation state
        if 'page' not in st.session_state:
            st.session_state.page = 'home'

        # Initialize admin state
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False

        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
            "📊 DASHBOARD": self.render_dashboard,
            "🎯 JOB SEARCH": self.render_job_search,
            "💬 FEEDBACK": self.render_feedback_page,
            "ℹ️ ABOUT": self.render_about,
        }

        # Initialize managers & backend services
        self.dashboard_manager = DashboardManager()
        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer(notifier=_st_notifier)
        self.builder = ResumeBuilder()
        self.job_roles = JOB_ROLES

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'
        if 'selected_role' not in st.session_state:
            st.session_state.selected_role = None

        # Initialize database
        init_database()

        # Load external CSS
        with open(STYLE_CSS_PATH, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

        # Load Google Fonts
        st.markdown("""
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)

        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = []
        if 'ai_analysis_stats' not in st.session_state:
            st.session_state.ai_analysis_stats = {
                'score_distribution': {},
                'total_analyses': 0,
                'average_score': 0,
            }

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL"""
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .feature-card {
            background-color: #1e1e1e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def add_footer(self):
        """Add a footer to all pages"""
        st.markdown("<hr style='margin-top: 50px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 3, 1])

        with col2:
            st.markdown("""
            <p style='text-align: center;'>
                Powered by <b>Streamlit</b> and <b>Google Gemini AI</b> | Developed by
                <a href="https://www.linkedin.com/in/latamishra5/" target="_blank" style='text-decoration: none; color: #FFFFFF'>
                    <b>Lata Mishra</b>
                </a>
            </p>
            """, unsafe_allow_html=True)

    def export_to_excel(self):
        """Export resume data to Excel"""
        return self.dashboard_manager.service.export_to_openpyxl_excel()

    def render_dashboard(self):
        """Render the dashboard page"""
        render_dashboard(self.dashboard_manager)

    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return render_empty_state(icon, message)

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])

        if uploaded_file is not None:
            try:
                if uploaded_file.type == "application/pdf":
                    resume_text = self.analyzer.extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = self.analyzer.extract_text_from_docx(uploaded_file)

                st.session_state.resume_data = {
                    'filename': uploaded_file.name,
                    'content': resume_text,
                    'upload_time': datetime.now().isoformat(),
                }

                self.analyze_resume(resume_text)
                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_builder(self):
        render_builder(self.builder)

    def render_about(self):
        render_about()

    def render_analyzer(self):
        render_analyzer(self.analyzer, self.ai_analyzer, self.job_roles)

    def render_home(self):
        render_home()

    def render_job_search(self):
        render_job_search_page()

    def render_feedback_page(self):
        render_feedback_page()

    def show_repo_notification(self):
        message = """
<div style="background-color: #1e1e1e; border-radius: 10px; border: 1px solid #4b6cb7; padding: 10px; margin: 10px 0; color: white;">
    <div style="margin-bottom: 10px;">Check out these other repositories:</div>
    <div style="margin-bottom: 5px;"><b>Hacking Resources:</b></div>
    <ul style="margin-top: 0; padding-left: 20px;">
        <li><a href="https://github.com/latamishra5/tryhackme-free-rooms" target="_blank" style="color: #4CAF50;">TryHackMe Free Rooms</a></li>
        <li><a href="https://github.com/latamishra5/Awesome-Hacking" target="_blank" style="color: #4CAF50;">Awesome Hacking</a></li>
    </ul>
    <div style="margin-bottom: 5px;"><b>Programming Languages:</b></div>
    <ul style="margin-top: 0; padding-left: 20px;">
        <li><a href="https://github.com/latamishra5/Awesome-Java" target="_blank" style="color: #4CAF50;">Awesome Java</a></li>
        <li><a href="https://github.com/latamishra5/30-Days-Of-Rust" target="_blank" style="color: #4CAF50;">30 Days Of Rust</a></li>
    </ul>
    <div style="margin-bottom: 5px;"><b>Data Structures & Algorithms:</b></div>
    <ul style="margin-top: 0; padding-left: 20px;">
        <li><a href="https://github.com/latamishra5/GeeksforGeeks-POTD" target="_blank" style="color: #4CAF50;">GeeksforGeeks POTD</a></li>
        <li><a href="https://github.com/latamishra5/Leetcode-POTD" target="_blank" style="color: #4CAF50;">Leetcode POTD</a></li>
    </ul>
    <div style="margin-bottom: 5px;"><b>AI/ML Projects:</b></div>
    <ul style="margin-top: 0; padding-left: 20px;">
        <li><a href="https://github.com/latamishra5/AI-Nexus" target="_blank" style="color: #4CAF50;">AI Nexus</a></li>
    </ul>
"""
        st.sidebar.markdown(message, unsafe_allow_html=True)

    def main(self):
        """Main application entry point"""
        self.apply_global_styles()

        with st.sidebar:
            st.title("Resume Analyzer(AI)")
            st.markdown("---")

            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = (
                        page_name.lower()
                        .replace(" ", "_")
                        .replace("🏠", "")
                        .replace("🔍", "")
                        .replace("📝", "")
                        .replace("📊", "")
                        .replace("🎯", "")
                        .replace("💬", "")
                        .replace("ℹ️", "")
                        .strip()
                    )
                    st.session_state.page = cleaned_name
                    st.rerun()

            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("---")

            if st.session_state.get('is_admin', False):
                st.success(f"Logged in as: {st.session_state.get('current_admin_email')}")
                if st.button("Logout", key="logout_button"):
                    try:
                        log_admin_action(st.session_state.get('current_admin_email'), "logout")
                        st.session_state.is_admin = False
                        st.session_state.current_admin_email = None
                        st.success("Logged out successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during logout: {str(e)}")
            else:
                with st.expander("👤 Admin Login"):
                    admin_email_input = st.text_input("Email", key="admin_email_input")
                    admin_password = st.text_input("Password", type="password", key="admin_password_input")
                    if st.button("Login", key="login_button"):
                        try:
                            if verify_admin(admin_email_input, admin_password):
                                st.session_state.is_admin = True
                                st.session_state.current_admin_email = admin_email_input
                                log_admin_action(admin_email_input, "login")
                                st.success("Logged in successfully!")
                                st.rerun()
                            else:
                                st.error("Invalid credentials")
                        except Exception as e:
                            st.error(f"Error during login: {str(e)}")

            self.show_repo_notification()

        # Force home page on first load
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()

        current_page = st.session_state.get('page', 'home')

        page_mapping = {
            name.lower()
            .replace(" ", "_")
            .replace("🏠", "")
            .replace("🔍", "")
            .replace("📝", "")
            .replace("📊", "")
            .replace("🎯", "")
            .replace("💬", "")
            .replace("ℹ️", "")
            .strip(): name
            for name in self.pages.keys()
        }

        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            self.render_home()

        self.add_footer()


def main():
    """Run the Streamlit application."""
    configure_page()
    app = ResumeApp()
    app.main()


if __name__ == "__main__":
    main()
