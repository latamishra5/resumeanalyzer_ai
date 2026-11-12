"""
Resume Analyzer(AI) - Public Frontend Application Coordinator
"""

from pathlib import Path
import sys

# Ensure project root is importable if launched directly via `streamlit run frontend/app.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import html
import streamlit as st

from backend.analyzers.ai_resume_analyzer import AIResumeAnalyzer
from backend.analyzers.resume_analyzer import ResumeAnalyzer
from backend.auth.auth_service import AuthService
from backend.builders.resume_builder import ResumeBuilder
from backend.config.job_roles import JOB_ROLES
from backend.config.logging_config import configure_logging
from backend.config.settings import STYLE_CSS_PATH
from backend.database.connection import init_database
from frontend.components.auth_ui import AuthUI
from frontend.pages.about import render_about
from frontend.pages.analyzer import _st_notifier, render_analyzer
from frontend.pages.builder import render_builder
from frontend.pages.dashboard import DashboardManager, render_dashboard
from frontend.pages.feedback import render_feedback_page
from frontend.pages.home import render_home
from frontend.pages.job_search import render_job_search_page


def configure_page():
    """Configure Streamlit page settings (must run before any other st.* call)."""
    st.set_page_config(
        page_title="Resume Analyzer(AI) | ATS & Career Platform",
        page_icon=":material/description:",
        layout="wide",
    )


class ResumeApp:
    def __init__(self):
        """Initialize the public Streamlit SaaS coordinator."""
        configure_logging()

        if "form_data" not in st.session_state:
            st.session_state.form_data = {
                "personal_info": {
                    "full_name": "",
                    "email": "",
                    "phone": "",
                    "location": "",
                    "linkedin": "",
                    "portfolio": "",
                },
                "summary": "",
                "experiences": [],
                "education": [],
                "projects": [],
                "skills_categories": {
                    "technical": [],
                    "soft": [],
                    "languages": [],
                    "tools": [],
                },
            }

        if "page" not in st.session_state:
            st.session_state.page = "home"

        self.nav_items = [
            ("home", "Home", ":material/home:", self.render_home),
            ("resume_analyzer", "Resume Analyzer", ":material/manage_search:", self.render_analyzer),
            ("resume_builder", "Resume Builder", ":material/edit_document:", self.render_builder),
            ("dashboard", "Dashboard", ":material/analytics:", self.render_dashboard),
            ("job_search", "Job Search", ":material/work:", self.render_job_search),
            ("feedback", "Feedback", ":material/feedback:", self.render_feedback_page),
            ("about", "About", ":material/info:", self.render_about),
        ]
        self.pages = {label: handler for _, label, _, handler in self.nav_items}

        self.dashboard_manager = DashboardManager()
        self.analyzer = ResumeAnalyzer()
        self.ai_analyzer = AIResumeAnalyzer(notifier=_st_notifier)
        self.builder = ResumeBuilder()
        self.auth_service = AuthService()
        self.auth_ui = AuthUI(self.auth_service)
        self.job_roles = JOB_ROLES

        if "user_id" not in st.session_state:
            st.session_state.user_id = "default_user"
        if "selected_role" not in st.session_state:
            st.session_state.selected_role = None

        init_database()

        token = st.session_state.get("session_token")
        if token and not st.session_state.get("authenticated"):
            verified = self.auth_service.verify_session(token)
            if verified:
                st.session_state.update(verified)

        with open(STYLE_CSS_PATH, encoding="utf-8") as css_file:
            st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

        st.markdown(
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">',
            unsafe_allow_html=True,
        )

        if "resume_data" not in st.session_state:
            st.session_state.resume_data = []
        if "ai_analysis_stats" not in st.session_state:
            st.session_state.ai_analysis_stats = {
                "score_distribution": {},
                "total_analyses": 0,
                "average_score": 0,
            }

    def add_footer(self):
        """Render clean SaaS footer across pages."""
        st.markdown("<hr style='margin-top: 48px; margin-bottom: 16px; border-color: rgba(148,163,184,0.16);'>", unsafe_allow_html=True)
        st.markdown(
            """
            <p style="text-align: center; color: #94a3b8; font-size: 0.88rem;">
                Resume Analyzer(AI) &mdash; ATS Screening, AI Resume Analysis &amp; Career Optimization Platform
            </p>
            """,
            unsafe_allow_html=True,
        )

    def render_dashboard(self):
        render_dashboard(self.dashboard_manager)

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

    def render_sidebar_info(self):
        """Render account quick controls and platform capabilities summary in the sidebar."""
        is_authed = bool(
            st.session_state.get("authenticated") and isinstance(st.session_state.get("user_id"), int)
        )
        if is_authed:
            display_name = html.escape(
                str(st.session_state.get("full_name") or st.session_state.get("username") or "Member"),
                quote=True,
            )
            st.sidebar.markdown(
                f"""
                <div class="sidebar-brand-card" style="margin-bottom: 10px;">
                    <strong>Signed in: {display_name}</strong>
                    <span>Your resumes, ATS scores, and AI reports sync to your private workspace.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_prof, col_out = st.sidebar.columns(2)
            with col_prof:
                if st.button("My Account", icon=":material/account_circle:", key="nav_profile", width="stretch"):
                    st.session_state.page = "profile"
                    st.rerun()
            with col_out:
                if st.button("Sign Out", icon=":material/logout:", key="nav_signout", width="stretch"):
                    self.auth_service.logout_user(
                        session_token=st.session_state.get("session_token"),
                        user_id=st.session_state.get("user_id"),
                    )
                    for auth_key in (
                        "authenticated",
                        "username",
                        "email",
                        "full_name",
                        "session_token",
                        "redirect_to",
                    ):
                        st.session_state.pop(auth_key, None)
                    st.session_state.user_id = "default_user"
                    st.session_state.page = "home"
                    st.rerun()
        else:
            col_in, col_up = st.sidebar.columns(2)
            with col_in:
                if st.button("Sign In", icon=":material/login:", key="nav_login", width="stretch"):
                    st.session_state.page = "login"
                    st.rerun()
            with col_up:
                if st.button("Sign Up", icon=":material/person_add:", key="nav_signup", width="stretch"):
                    st.session_state.page = "signup"
                    st.rerun()

        st.sidebar.markdown(
            """
            <div class="sidebar-brand-card">
                <strong>ATS &amp; Career Platform</strong>
                <span>Upload resumes for instant ATS scoring, AI gap analysis, role tailoring, and DOCX/PDF generation.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _normalize_page_name(page_name: str) -> str:
        return "_".join(page_name.lower().strip().split())

    def main(self):
        """Main application entrypoint."""
        with st.sidebar:
            st.title("Resume Analyzer(AI)")
            st.caption("ATS Screening & Career Platform")
            st.markdown("---")

            for slug, label, icon, _handler in self.nav_items:
                if st.button(label, icon=icon, key=f"nav_{slug}", width="stretch"):
                    st.session_state.page = slug
                    st.rerun()

            st.markdown("---")
            self.render_sidebar_info()

        query_page = st.query_params.get("page")
        if isinstance(query_page, list):
            query_page = query_page[0] if query_page else None

        page_mapping = {
            slug: handler
            for slug, _label, _icon, handler in self.nav_items
        }
        page_mapping.update({
            "login": self.auth_ui.render_login_page,
            "signup": self.auth_ui.render_signup_page,
            "profile": self.auth_ui.render_profile_page,
        })
        page_aliases = {
            "analyzer": "resume_analyzer",
            "builder": "resume_builder",
        }

        if query_page:
            normalized_query = page_aliases.get(query_page.lower().strip(), query_page.lower().strip())
            if normalized_query in page_mapping:
                st.session_state.initial_load = True
                st.session_state.page = normalized_query
                st.query_params.clear()

        if "initial_load" not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = "home"
            st.rerun()

        current_page = st.session_state.get("page", "home")
        if current_page in page_mapping:
            page_mapping[current_page]()
        else:
            self.render_home()

        self.add_footer()


def main():
    """Run the public Streamlit application."""
    configure_page()
    app = ResumeApp()
    app.main()


if __name__ == "__main__":
    main()
