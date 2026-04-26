"""
Authentication UI Components for Resume Analyzer AI
Handles login, signup, and profile management interfaces
"""
import streamlit as st
import re
from auth.auth_manager import AuthManager

class AuthUI:
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def render_login_page(self):
        """Render login page"""
        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">Welcome Back</h1>
            <p class="header-subtitle">Login to access your Resume Analyzer AI account</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form", clear_on_submit=True):
                st.markdown("### 🔐 Login")
                
                # Username/Email field
                username_or_email = st.text_input(
                    "Username or Email",
                    placeholder="Enter your username or email",
                    help="You can use either your username or email to login"
                )
                
                # Password field
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )
                
                # Remember me checkbox
                remember_me = st.checkbox("Remember me for 30 days")
                
                # Submit button
                submitted = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    if not username_or_email or not password:
                        st.error("Please fill in all fields")
                    else:
                        success, message = self.auth_manager.login_user(username_or_email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            # Signup link
            st.markdown("---")
            st.markdown("### New to Resume Analyzer AI?")
            if st.button("📝 Create an Account", use_container_width=True):
                st.session_state['page'] = 'signup'
                st.rerun()
            
            # Forgot password link
            st.markdown("---")
            if st.button("🔑 Forgot Password?", use_container_width=True):
                st.info("Password reset feature coming soon!")
    
    def render_signup_page(self):
        """Render signup page"""
        st.markdown("""
        <div class="page-header">
            <h1 class="header-title">Create Account</h1>
            <p class="header-subtitle">Join Resume Analyzer AI and start optimizing your resume</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Signup form container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("signup_form", clear_on_submit=True):
                st.markdown("### 📝 Sign Up")
                
                # Account Information
                st.markdown("#### Account Information")
                
                username = st.text_input(
                    "Username *",
                    placeholder="Choose a unique username",
                    help="Username must be 3-20 characters long and contain only letters, numbers, and underscores"
                )
                
                email = st.text_input(
                    "Email *",
                    placeholder="Enter your email address",
                    help="We'll use this for account verification and notifications"
                )
                
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Create a strong password",
                    help="Password must be at least 8 characters long"
                )
                
                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Confirm your password"
                )
                
                # Personal Information
                st.markdown("#### Personal Information (Optional)")
                
                full_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name"
                )
                
                phone = st.text_input(
                    "Phone Number",
                    placeholder="Enter your phone number"
                )
                
                # Social Links
                st.markdown("#### Social Links (Optional)")
                
                linkedin = st.text_input(
                    "LinkedIn Profile",
                    placeholder="https://linkedin.com/in/yourprofile"
                )
                
                github = st.text_input(
                    "GitHub Profile",
                    placeholder="https://github.com/yourusername"
                )
                
                portfolio = st.text_input(
                    "Portfolio Website",
                    placeholder="https://yourportfolio.com"
                )
                
                # Terms and Conditions
                st.markdown("#### Terms and Conditions")
                agree_terms = st.checkbox(
                    "I agree to the Terms of Service and Privacy Policy *",
                    help="You must agree to the terms to create an account"
                )
                
                # Submit button
                submitted = st.form_submit_button(
                    "🚀 Create Account",
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    # Validation
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
                        # Create account
                        success, message = self.auth_manager.register_user(
                            username=username,
                            email=email,
                            password=password,
                            full_name=full_name,
                            phone=phone,
                            linkedin=linkedin,
                            github=github,
                            portfolio=portfolio
                        )
                        
                        if success:
                            st.success(message)
                            st.info("Please login with your new credentials")
                            st.session_state['page'] = 'login'
                            st.rerun()
                        else:
                            st.error(message)
            
            # Login link
            st.markdown("---")
            st.markdown("### Already have an account?")
            if st.button("🔐 Back to Login", use_container_width=True):
                st.session_state['page'] = 'login'
                st.rerun()
    
    def render_profile_page(self):
        """Render user profile page"""
        if 'user_id' not in st.session_state:
            st.error("Please login to view your profile")
            return
        
        user_id = st.session_state['user_id']
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
        
        # Profile container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Account Information Section
            st.markdown("### 📋 Account Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Username", profile['username'])
                st.metric("Email", profile['email'])
            
            with col2:
                st.metric("Member Since", profile['created_at'][:10] if profile['created_at'] else "N/A")
                st.metric("Last Login", profile['last_login'][:10] if profile['last_login'] else "Never")
            
            # Edit Profile Form
            st.markdown("---")
            st.markdown("### ✏️ Edit Profile")
            
            with st.form("edit_profile_form"):
                # Personal Information
                st.markdown("#### Personal Information")
                
                full_name = st.text_input(
                    "Full Name",
                    value=profile['full_name'] or "",
                    placeholder="Enter your full name"
                )
                
                phone = st.text_input(
                    "Phone Number",
                    value=profile['phone'] or "",
                    placeholder="Enter your phone number"
                )
                
                # Social Links
                st.markdown("#### Social Links")
                
                linkedin = st.text_input(
                    "LinkedIn Profile",
                    value=profile['linkedin'] or "",
                    placeholder="https://linkedin.com/in/yourprofile"
                )
                
                github = st.text_input(
                    "GitHub Profile",
                    value=profile['github'] or "",
                    placeholder="https://github.com/yourusername"
                )
                
                portfolio = st.text_input(
                    "Portfolio Website",
                    value=profile['portfolio'] or "",
                    placeholder="https://yourportfolio.com"
                )
                
                # Submit button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.form_submit_button("💾 Save Changes", use_container_width=True):
                        success, message = self.auth_manager.update_user_profile(
                            user_id=user_id,
                            full_name=full_name if full_name else None,
                            phone=phone if phone else None,
                            linkedin=linkedin if linkedin else None,
                            github=github if github else None,
                            portfolio=portfolio if portfolio else None
                        )
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            
            # Change Password Section
            st.markdown("---")
            st.markdown("### 🔐 Change Password")
            
            with st.form("change_password_form"):
                current_password = st.text_input(
                    "Current Password",
                    type="password",
                    placeholder="Enter your current password"
                )
                
                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Enter your new password"
                )
                
                confirm_new_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    placeholder="Confirm your new password"
                )
                
                # Submit button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.form_submit_button("🔄 Change Password", use_container_width=True):
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
                                new_password=new_password
                            )
                            
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
            
            # Activity History
            st.markdown("---")
            st.markdown("### 📊 Activity History")
            
            activities = self.auth_manager.get_user_activity(user_id, limit=10)
            
            if activities:
                for activity in activities:
                    st.markdown(f"""
                    <div style="padding: 10px; margin: 5px 0; background: #262626; border-radius: 8px; border-left: 4px solid #14b8a6;">
                        <strong>{activity['type'].title()}</strong> - {activity['timestamp'][:19]}
                        <br><small>{activity['details'] or 'No details available'}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No activity history available")
            
            # Logout Button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                    success, message = self.auth_manager.logout_user()
                    if success:
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
            st.markdown("### 🔒 Protected Content")
            st.info("This page requires you to be logged in. Please login or create an account to continue.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔐 Login", use_container_width=True):
                    st.session_state['page'] = 'login'
                    st.rerun()
            
            with col2:
                if st.button("📝 Sign Up", use_container_width=True):
                    st.session_state['page'] = 'signup'
                    st.rerun()
