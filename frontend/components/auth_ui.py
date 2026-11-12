"""
Authentication UI Components for Resume Analyzer AI
Handles login, signup, profile management interfaces, and Streamlit route guards.
"""

from functools import wraps
import html
import re
import streamlit as st

from backend.auth.auth_service import AuthService
from backend.database.connection import get_user_resumes_history


def require_auth(f):
    """Decorator to require authentication for a Streamlit page/view function."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_service = AuthService()
        session_token = st.session_state.get('session_token')
        session_user = auth_service.verify_session(session_token)
        if not session_user:
            st.session_state['redirect_to'] = st.session_state.get('page', 'home')
            st.session_state['page'] = 'login'
            st.error("Please login to access this page")
            st.rerun()
        st.session_state.update(session_user)
        return f(*args, **kwargs)
    return wrapper


class AuthUI:
    def __init__(self, auth_service=None):
        self.auth_manager = auth_service or AuthService()

    def render_login_page(self):
        """Render login page"""
        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">Welcome Back</h1>
            <p class="header-subtitle">Login to access your Resume Analyzer AI account</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.form("login_form", clear_on_submit=True):
                st.markdown("### Login")

                username_or_email = st.text_input(
                    "Username or Email",
                    placeholder="Enter your username or email",
                    help="You can use either your username or email to login",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                _remember_me = st.checkbox("Remember me for 30 days")

                submitted = st.form_submit_button(
                    "Login",
                    icon=":material/login:",
                    width="stretch",
                    type="primary",
                )

                if submitted:
                    if not username_or_email or not password:
                        st.error("Please fill in all fields")
                    else:
                        success, message, session_data = self.auth_manager.login_user(
                            username_or_email,
                            password,
                            ip_address=st.session_state.get('ip_address', 'unknown'),
                            user_agent=st.session_state.get('user_agent', 'unknown'),
                        )
                        if success:
                            if session_data:
                                st.session_state.update(session_data)
                            target_page = st.session_state.pop('redirect_to', 'home')
                            if target_page in ('login', 'signup', ''):
                                target_page = 'home'
                            st.session_state['page'] = target_page
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            st.markdown("---")
            st.markdown("### New to Resume Analyzer AI?")
            if st.button("Create an Account", icon=":material/person_add:", width="stretch"):
                st.session_state['page'] = 'signup'
                st.rerun()

            st.markdown("---")
            if st.button("Forgot Password?", icon=":material/key:", width="stretch"):
                st.info("Password reset feature coming soon!")

    def render_signup_page(self):
        """Render signup page"""
        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">Create Account</h1>
            <p class="header-subtitle">Join Resume Analyzer AI and start optimizing your resume</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            with st.form("signup_form", clear_on_submit=True):
                st.markdown("### Sign Up")

                st.markdown("#### Account Information")

                username = st.text_input(
                    "Username *",
                    placeholder="Choose a unique username",
                    help="Username must be 3-20 characters long and contain only letters, numbers, and underscores",
                )

                email = st.text_input(
                    "Email *",
                    placeholder="Enter your email address",
                    help="We'll use this for account verification and notifications",
                )

                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Create a strong password",
                    help="Password must be at least 8 characters long",
                )

                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Confirm your password",
                )

                st.markdown("#### Personal Information (Optional)")

                full_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name",
                )

                phone = st.text_input(
                    "Phone Number",
                    placeholder="Enter your phone number",
                )

                st.markdown("#### Social Links (Optional)")

                linkedin = st.text_input(
                    "LinkedIn Profile",
                    placeholder="https://linkedin.com/in/yourprofile",
                )

                github = st.text_input(
                    "GitHub Profile",
                    placeholder="https://github.com/yourusername",
                )

                portfolio = st.text_input(
                    "Portfolio Website",
                    placeholder="https://yourportfolio.com",
                )

                st.markdown("#### Terms and Conditions")
                agree_terms = st.checkbox(
                    "I agree to the Terms of Service and Privacy Policy *",
                    help="You must agree to the terms to create an account",
                )

                submitted = st.form_submit_button(
                    "Create Account",
                    icon=":material/person_add:",
                    width="stretch",
                    type="primary",
                )

                if submitted:
                    errors = []

                    if not username or not email or not password or not confirm_password:
                        errors.append("Please fill in all required fields")

                    if not self.validate_username(username):
                        errors.append("Username must be 3-20 characters long and contain only letters, numbers, and underscores")

                    if not self.validate_email(email):
                        errors.append("Please enter a valid email address")

                    if len(password) < 8:
                        errors.append("Password must be at least 8 characters long")

                    if password != confirm_password:
                        errors.append("Passwords do not match")

                    if not agree_terms:
                        errors.append("You must agree to the terms and conditions")

                    if linkedin and not self.validate_url(linkedin):
                        errors.append("Please enter a valid LinkedIn URL")

                    if github and not self.validate_url(github):
                        errors.append("Please enter a valid GitHub URL")

                    if portfolio and not self.validate_url(portfolio):
                        errors.append("Please enter a valid portfolio URL")

                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        success, message = self.auth_manager.register_user(
                            username=username,
                            email=email,
                            password=password,
                            full_name=full_name,
                            phone=phone,
                            linkedin=linkedin,
                            github=github,
                            portfolio=portfolio,
                            ip_address=st.session_state.get('ip_address', 'unknown'),
                        )

                        if success:
                            st.success(message)
                            st.info("Please login with your new credentials")
                            st.session_state['page'] = 'login'
                            st.rerun()
                        else:
                            st.error(message)

            st.markdown("---")
            st.markdown("### Already have an account?")
            if st.button("Back to Login", icon=":material/login:", width="stretch"):
                st.session_state['page'] = 'login'
                st.rerun()

    def render_profile_page(self):
        """Render user profile page"""
        user_id = st.session_state.get('user_id')
        if not st.session_state.get('authenticated') or not isinstance(user_id, int):
            st.error("Please login to view your profile")
            if st.button("Go to Login", icon=":material/login:"):
                st.session_state['page'] = 'login'
                st.rerun()
            return

        profile = self.auth_manager.get_user_profile(user_id)

        if not profile:
            st.error("Profile not found")
            return

        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">My Profile</h1>
            <p class="header-subtitle">Manage your account settings and personal information</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### :material/badge: Account Information")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Username", profile['username'])
                st.metric("Email", profile['email'])

            with col2:
                st.metric("Member Since", profile['created_at'][:10] if profile['created_at'] else "N/A")
                st.metric("Last Login", profile['last_login'][:10] if profile['last_login'] else "Never")

            st.markdown("---")
            st.markdown("### :material/edit: Edit Profile")

            with st.form("edit_profile_form"):
                st.markdown("#### Personal Information")

                full_name = st.text_input(
                    "Full Name",
                    value=profile['full_name'] or "",
                    placeholder="Enter your full name",
                )

                phone = st.text_input(
                    "Phone Number",
                    value=profile['phone'] or "",
                    placeholder="Enter your phone number",
                )

                st.markdown("#### Social Links")

                linkedin = st.text_input(
                    "LinkedIn Profile",
                    value=profile['linkedin'] or "",
                    placeholder="https://linkedin.com/in/yourprofile",
                )

                github = st.text_input(
                    "GitHub Profile",
                    value=profile['github'] or "",
                    placeholder="https://github.com/yourusername",
                )

                portfolio = st.text_input(
                    "Portfolio Website",
                    value=profile['portfolio'] or "",
                    placeholder="https://yourportfolio.com",
                )

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.form_submit_button("Save Changes", icon=":material/save:", width="stretch"):
                        success, message = self.auth_manager.update_user_profile(
                            user_id=user_id,
                            full_name=full_name if full_name else None,
                            phone=phone if phone else None,
                            linkedin=linkedin if linkedin else None,
                            github=github if github else None,
                            portfolio=portfolio if portfolio else None,
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

            st.markdown("---")
            st.markdown("### :material/lock_reset: Change Password")

            with st.form("change_password_form"):
                current_password = st.text_input(
                    "Current Password",
                    type="password",
                    placeholder="Enter your current password",
                )

                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter your new password",
                )

                confirm_new_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Confirm your new password",
                )

                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.form_submit_button("Change Password", icon=":material/sync:", width="stretch"):
                        if not current_password or not new_password or not confirm_new_password:
                            st.error("Please fill in all fields")
                        elif new_password != confirm_new_password:
                            st.error("New passwords do not match")
                        elif len(new_password) < 8:
                            st.error("New password must be at least 8 characters long")
                        else:
                            success, message = self.auth_manager.change_password(
                                user_id=user_id,
                                current_password=current_password,
                                new_password=new_password,
                            )

                            if success:
                                st.success(message)
                            else:
                                st.error(message)

            st.markdown("---")
            st.markdown("### :material/description: My Resume & Analysis History")
            history = get_user_resumes_history(user_id, limit=15)
            if history:
                for entry in history:
                    role_label = html.escape(str(entry.get("target_role") or "General Role"), quote=True)
                    name_label = html.escape(str(entry.get("name") or "Untitled Resume"), quote=True)
                    ats_txt = f"{entry['ats_score']:.1f}%" if entry.get("ats_score") is not None else "Builder Draft"
                    created_txt = html.escape(str(entry.get("created_at") or "")[:16], quote=True)
                    st.markdown(
                        f"""
                        <div style="padding: 10px 12px; margin: 6px 0; background: #1f2937; border-radius: 8px; border-left: 4px solid #38bdf8;">
                            <strong>{name_label}</strong> &middot; {role_label}
                            <span style="float: right; color: #34d399; font-weight: 600;">{ats_txt}</span>
                            <br><small style="color: #9ca3af;">Saved: {created_txt}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No saved resumes or analyses yet. Analyze or build a resume while signed in to save it here.")

            st.markdown("---")
            st.markdown("### :material/history: Activity History")

            activities = self.auth_manager.get_user_activity(user_id, limit=10)

            if activities:
                for activity in activities:
                    act_type = html.escape(str(activity['type']).title(), quote=True)
                    act_ts = html.escape(str(activity['timestamp'])[:19], quote=True)
                    act_details = html.escape(str(activity['details'] or 'No details available'), quote=True)
                    st.markdown(f"""
                    <div style="padding: 10px; margin: 5px 0; background: #262626; border-radius: 8px; border-left: 4px solid #14b8a6;">
                        <strong>{act_type}</strong> - {act_ts}
                        <br><small>{act_details}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No activity history available")

            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Logout", icon=":material/logout:", width="stretch", type="secondary"):
                    success, message = self.auth_manager.logout_user(
                        session_token=st.session_state.get('session_token'),
                        user_id=st.session_state.get('user_id'),
                        ip_address=st.session_state.get('ip_address', 'unknown'),
                    )
                    if success:
                        for auth_key in (
                            'authenticated',
                            'username',
                            'email',
                            'full_name',
                            'session_token',
                            'redirect_to',
                        ):
                            st.session_state.pop(auth_key, None)
                        st.session_state['user_id'] = 'default_user'
                        st.session_state['page'] = 'home'
                        st.session_state['initial_load'] = True
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    def validate_username(self, username):
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 20:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

    def validate_email(self, email):
        """Validate email format"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_url(self, url):
        """Validate URL format"""
        if not url:
            return True  # Optional field
        pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return bool(re.match(pattern, url))

    def render_auth_required_page(self):
        """Render page when authentication is required"""
        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">Authentication Required</h1>
            <p class="header-subtitle">Please login or create an account to access this feature</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown("### :material/lock: Protected Content")
            st.info("This page requires you to be logged in. Please login or create an account to continue.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", icon=":material/login:", width="stretch"):
                    st.session_state['page'] = 'login'
                    st.rerun()

            with col2:
                if st.button("Sign Up", icon=":material/person_add:", width="stretch"):
                    st.session_state['page'] = 'signup'
                    st.rerun()
