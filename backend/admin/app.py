"""
Resume Analyzer(AI) - Standalone Backend Admin Portal

Run directly:
    python run_admin.py
    # or:
    streamlit run backend/admin/app.py --server.port 8502
"""

from datetime import datetime
import html
from pathlib import Path
import sys

# Ensure project root is importable when invoked via `streamlit run backend/admin/app.py`
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.admin.service import AdminService
from backend.config.logging_config import configure_logging


def configure_page():
    """Configure standalone Admin Portal page settings."""
    st.set_page_config(
        page_title="Admin Portal | Resume Analyzer(AI)",
        page_icon=":material/admin_panel_settings:",
        layout="wide",
    )


def _apply_admin_styles():
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        <style>
        .admin-hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #064e3b 100%);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        }
        .admin-hero h1 {
            margin: 0;
            color: #ffffff;
            font-size: 2rem;
            font-weight: 700;
        }
        .admin-hero p {
            margin: 0.35rem 0 0 0;
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.98rem;
        }
        .admin-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: rgba(16, 185, 129, 0.16);
            border: 1px solid #10b981;
            color: #6ee7b7;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_exports(service: AdminService, df: pd.DataFrame, prefix: str, sheet_name: str):
    """Render standardized Excel / CSV / JSON download controls for a DataFrame."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Export Excel",
            icon=":material/table_view:",
            data=service.export_dataframe_excel(df, sheet_name=sheet_name),
            file_name=f"{prefix}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{prefix}_dl_xlsx",
            width="stretch",
        )
    with col2:
        st.download_button(
            "Export CSV",
            icon=":material/csv:",
            data=service.export_dataframe_csv(df),
            file_name=f"{prefix}_{timestamp}.csv",
            mime="text/csv",
            key=f"{prefix}_dl_csv",
            width="stretch",
        )
    with col3:
        st.download_button(
            "Export JSON",
            icon=":material/data_object:",
            data=service.export_dataframe_json(df),
            file_name=f"{prefix}_{timestamp}.json",
            mime="application/json",
            key=f"{prefix}_dl_json",
            width="stretch",
        )


def _render_auth_gate(service: AdminService):
    """Render first-time admin setup or login screen when unauthenticated."""
    st.markdown(
        """
        <div class="admin-hero">
            <span class="admin-badge"><i class="fas fa-shield-alt"></i> BACKEND ADMIN PORTAL</span>
            <h1>Resume Analyzer(AI) — Admin Console</h1>
            <p>Isolated administrative backend. Public frontend users cannot access these controls.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        if not service.has_any_admin():
            st.warning("No admin account is configured yet. Create your initial admin account below.")
            with st.form("admin_initial_setup_form"):
                st.subheader(":material/person_add: First-Time Admin Setup")
                email = st.text_input("Admin Email", placeholder="admin@yourdomain.com")
                password = st.text_input("Password (min 8 chars)", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button(
                    "Create Admin & Sign In",
                    icon=":material/login:",
                    type="primary",
                    width="stretch",
                )

                if submitted:
                    if password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = service.add_admin(email, password)
                        if ok:
                            normalized = email.strip()
                            service.log_admin_action(normalized, "initial_admin_setup")
                            service.log_admin_action(normalized, "login")
                            st.session_state["admin_authenticated"] = True
                            st.session_state["admin_email"] = normalized
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            st.caption("Tip: You can also configure `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` or run `scripts/create_admin.py`.")
        else:
            with st.form("admin_portal_login_form"):
                st.subheader(":material/verified_user: Admin Sign In")
                email = st.text_input("Admin Email", placeholder="admin@yourdomain.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign In",
                    icon=":material/login:",
                    type="primary",
                    width="stretch",
                )

                if submitted:
                    if service.verify_admin(email, password):
                        normalized = email.strip()
                        st.session_state["admin_authenticated"] = True
                        st.session_state["admin_email"] = normalized
                        service.log_admin_action(normalized, "login")
                        st.success("Signed in successfully.")
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials.")


def _render_overview_tab(service: AdminService):
    st.subheader(":material/dashboard: System Overview")
    overview = service.get_system_overview()

    row1 = st.columns(4)
    row1[0].metric("Total Resumes", overview["total_resumes"], f"+{overview['today_submissions']} today")
    row1[1].metric("Avg ATS Score", f"{overview['avg_ats_score']}%")
    row1[2].metric("AI Analyses", overview["ai_total_analyses"], f"Avg {overview['ai_avg_score']}/100")
    row1[3].metric("User Feedback", overview["total_feedback"], f"{overview['avg_feedback_rating']}/5 avg")

    row2 = st.columns(4)
    row2[0].metric("Standard Analyses", overview["total_analyses"])
    row2[1].metric("Registered Users", overview["total_users"])
    row2[2].metric("Resume DB Size", overview["resume_db_size"])
    row2[3].metric("Feedback DB Size", overview["feedback_db_size"])

    ai_stats = service.get_detailed_ai_stats()
    resumes_df = service.get_all_resumes_dataframe()

    col_left, col_right = st.columns(2)
    with col_left:
        if not resumes_df.empty and resumes_df["Target Role"].dropna().any():
            role_counts = (
                resumes_df["Target Role"]
                .fillna("Unspecified")
                .replace("", "Unspecified")
                .value_counts()
                .head(8)
                .reset_index()
            )
            role_counts.columns = ["Target Role", "Resumes"]
            fig = px.bar(
                role_counts,
                x="Target Role",
                y="Resumes",
                title="Top Target Roles (Resume Submissions)",
                color="Resumes",
                color_continuous_scale="Tealgrn",
            )
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No resume submissions yet to chart target roles.")

    with col_right:
        if ai_stats["model_usage"]:
            model_df = pd.DataFrame(ai_stats["model_usage"])
            fig = px.pie(
                model_df,
                names="model",
                values="count",
                title="AI Model Usage Breakdown",
                hole=0.45,
            )
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No AI analyses recorded yet.")


def _render_resumes_tab(service: AdminService, actor_email: str):
    st.subheader(":material/description: Resume Submissions & Data Export")
    df = service.get_all_resumes_dataframe()

    if df.empty:
        st.info("No resume submissions found in the database.")
        return

    fcol1, fcol2, fcol3 = st.columns(3)
    roles = ["All"] + sorted({str(v) for v in df["Target Role"].dropna() if str(v).strip()})
    categories = ["All"] + sorted({str(v) for v in df["Target Category"].dropna() if str(v).strip()})

    with fcol1:
        selected_role = st.selectbox("Filter by Target Role", roles, key="admin_resume_role_filter")
    with fcol2:
        selected_category = st.selectbox("Filter by Category", categories, key="admin_resume_cat_filter")
    with fcol3:
        search_text = st.text_input("Search Name / Email", key="admin_resume_search").strip().lower()

    filtered = df.copy()
    if selected_role != "All":
        filtered = filtered[filtered["Target Role"].astype(str) == selected_role]
    if selected_category != "All":
        filtered = filtered[filtered["Target Category"].astype(str) == selected_category]
    if search_text:
        mask = (
            filtered["Name"].fillna("").astype(str).str.lower().str.contains(search_text, regex=False)
            | filtered["Email"].fillna("").astype(str).str.lower().str.contains(search_text, regex=False)
        )
        filtered = filtered[mask]

    display_cols = [
        "ID", "Name", "Email", "Phone", "Target Role", "Target Category",
        "ATS Score", "Keyword Match", "Format Score", "Section Score", "Submission Date",
    ]
    display_df = filtered[display_cols].copy()
    for score_col in ("ATS Score", "Keyword Match", "Format Score", "Section Score"):
        display_df[score_col] = display_df[score_col].apply(
            lambda x: f"{float(x) * 100:.1f}%" if pd.notnull(x) and float(x) <= 1.0 else (
                f"{float(x):.1f}%" if pd.notnull(x) else "N/A"
            )
        )

    st.caption(f"Showing {len(filtered)} of {len(df)} resume submissions")
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.markdown("#### Export Resume Data")
    _render_exports(service, filtered, prefix="resumes_filtered", sheet_name="Resume Data")

    st.markdown("#### Inspect or Delete a Submission")
    record_ids = filtered["ID"].tolist()
    if record_ids:
        selected_id = st.selectbox("Select Resume ID", record_ids, key="admin_selected_resume_id")
        record = filtered[filtered["ID"] == selected_id].iloc[0]
        with st.expander(f"Details for #{selected_id} — {record['Name']} ({record['Email']})"):
            st.write("**Summary:**", record.get("Summary") or "—")
            st.write("**Skills:**", record.get("Skills") or "—")
            st.write("**Missing Skills:**", record.get("Missing Skills") or "—")
            st.write("**Recommendations:**", record.get("Recommendations") or "—")

        confirm_del = st.checkbox(
            f"Confirm permanent deletion of resume #{selected_id}",
            key="admin_confirm_delete_resume",
        )
        if st.button(
            "Delete Selected Resume",
            icon=":material/delete:",
            key="admin_delete_resume_btn",
            type="secondary",
        ):
            if not confirm_del:
                st.warning("Check the confirmation box first.")
            else:
                ok, msg = service.delete_resume_record(int(selected_id), actor_email)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def _render_ai_tab(service: AdminService, actor_email: str):
    st.subheader(":material/smart_toy: AI Analyzer Usage & Statistics")
    ai_stats = service.get_detailed_ai_stats()

    if ai_stats["total_analyses"] == 0:
        st.info("No AI analysis statistics recorded yet.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total AI Analyses", ai_stats["total_analyses"])
        c2.metric("Average AI Score", f"{ai_stats['average_score']}/100")
        top_model = ai_stats["model_usage"][0]["model"] if ai_stats["model_usage"] else "N/A"
        c3.metric("Most Used Model", top_model)

        col1, col2 = st.columns(2)
        with col1:
            dist_df = pd.DataFrame(ai_stats["score_distribution"])
            fig_dist = px.bar(
                dist_df,
                x="range",
                y="count",
                title="AI Score Distribution",
                labels={"range": "Score Bucket", "count": "Analyses"},
            )
            fig_dist.update_layout(height=320)
            st.plotly_chart(fig_dist, width="stretch")

        with col2:
            if ai_stats["daily_trend"]:
                trend_df = pd.DataFrame(ai_stats["daily_trend"])
                fig_trend = go.Figure(
                    go.Scatter(
                        x=trend_df["date"],
                        y=trend_df["count"],
                        mode="lines+markers",
                        name="Daily AI Analyses",
                    )
                )
                fig_trend.update_layout(title="Daily AI Analyses (Last 30 Days)", height=320)
                st.plotly_chart(fig_trend, width="stretch")

        st.markdown("#### Recent AI Analyses")
        st.dataframe(pd.DataFrame(ai_stats["recent_analyses"]), width="stretch", hide_index=True)

    st.divider()
    st.markdown("#### Danger Zone — Reset AI Statistics")
    confirm_reset = st.checkbox(
        "Confirm truncating all `ai_analysis` statistics",
        key="admin_confirm_reset_ai_stats",
    )
    if st.button("Reset AI Analysis Statistics", icon=":material/restart_alt:", key="admin_reset_ai_stats_btn"):
        if not confirm_reset:
            st.warning("Check the confirmation box before resetting statistics.")
        else:
            ok, msg = service.reset_ai_stats(actor_email)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)


def _render_feedback_tab(service: AdminService, actor_email: str):
    st.subheader(":material/feedback: User Feedback Management")
    df = service.get_feedback_dataframe()

    if df.empty:
        st.info("No user feedback submissions yet.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Responses", len(df))
    m2.metric("Avg Rating", f"{df['Rating'].mean():.2f} / 5")
    m3.metric("Avg Usability", f"{df['Usability Score'].mean():.2f} / 5")
    m4.metric("Avg Satisfaction", f"{df['Feature Satisfaction'].mean():.2f} / 5")

    st.dataframe(df, width="stretch", hide_index=True)
    _render_exports(service, df, prefix="feedback_export", sheet_name="User Feedback")

    st.markdown("#### Delete Feedback Entry")
    fb_id = st.selectbox("Select Feedback ID", df["ID"].tolist(), key="admin_feedback_id_select")
    if st.button("Delete Feedback Entry", icon=":material/delete:", key="admin_delete_feedback_btn"):
        ok, msg = service.delete_feedback_entry(int(fb_id), actor_email)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


def _render_users_tab(service: AdminService, actor_email: str):
    st.subheader(":material/group: Registered Users & Activity")
    users_df = service.get_users_dataframe()

    if users_df.empty:
        st.info("No registered application users found yet.")
    else:
        st.dataframe(users_df, width="stretch", hide_index=True)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            uid = st.selectbox("Select User ID", users_df["ID"].tolist(), key="admin_user_select")
        with col2:
            if st.button("Activate User", icon=":material/check_circle:", key="admin_activate_user", width="stretch"):
                ok, msg = service.set_user_active(int(uid), True, actor_email)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()
        with col3:
            if st.button("Deactivate User", icon=":material/block:", key="admin_deactivate_user", width="stretch"):
                ok, msg = service.set_user_active(int(uid), False, actor_email)
                st.success(msg) if ok else st.error(msg)
                if ok:
                    st.rerun()

    st.markdown("#### Recent User Activity")
    activity_df = service.get_user_activity_dataframe()
    if activity_df.empty:
        st.info("No user activity logs recorded yet.")
    else:
        st.dataframe(activity_df, width="stretch", hide_index=True)


def _render_admin_accounts_tab(service: AdminService, actor_email: str):
    st.subheader(":material/admin_panel_settings: Admin Accounts & Audit Logs")

    col_accounts, col_forms = st.columns([1.2, 1])
    with col_accounts:
        st.markdown("#### Database Admin Accounts")
        admins = service.list_admins()
        if admins:
            st.dataframe(pd.DataFrame(admins), width="stretch", hide_index=True)
        else:
            st.info("No database admin rows (currently using environment `ADMIN_EMAIL` / `ADMIN_PASSWORD`).")

        if service.has_env_admin():
            st.caption("Environment fallback admin (`ADMIN_EMAIL`) is active.")

        if admins:
            del_email = st.selectbox(
                "Remove Database Admin",
                [a["email"] for a in admins],
                key="admin_delete_email_select",
            )
            if st.button("Delete Selected Admin", icon=":material/delete:", key="admin_delete_account_btn"):
                ok, msg = service.delete_admin(del_email, actor_email=actor_email)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with col_forms:
        with st.form("add_admin_form", clear_on_submit=True):
            st.markdown("#### Add New Admin")
            new_email = st.text_input("Email")
            new_pw = st.text_input("Password (min 8 chars)", type="password")
            if st.form_submit_button("Create Admin", icon=":material/person_add:", width="stretch"):
                ok, msg = service.add_admin(new_email, new_pw, actor_email=actor_email)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        if admins:
            with st.form("update_admin_pw_form", clear_on_submit=True):
                st.markdown("#### Update Admin Password")
                target_email = st.selectbox("Admin Email", [a["email"] for a in admins])
                updated_pw = st.text_input("New Password (min 8 chars)", type="password")
                if st.form_submit_button("Update Password", icon=":material/key:", width="stretch"):
                    ok, msg = service.update_admin_password(target_email, updated_pw, actor_email=actor_email)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.divider()
    st.markdown("#### Admin Audit Logs")
    logs_df = service.get_admin_logs_dataframe()
    if logs_df.empty:
        st.info("No admin audit logs recorded yet.")
    else:
        st.dataframe(logs_df, width="stretch", hide_index=True)
        _render_exports(service, logs_df, prefix="admin_logs", sheet_name="Admin Logs")
        confirm_clear = st.checkbox("Confirm clearing audit logs", key="admin_confirm_clear_logs")
        if st.button("Clear Admin Logs", icon=":material/cleaning_services:", key="admin_clear_logs_btn"):
            if not confirm_clear:
                st.warning("Check confirmation before clearing audit logs.")
            else:
                ok, msg = service.clear_admin_logs(actor_email)
                if ok:
                    st.success(msg)
                    st.rerun()


def render_admin_portal(service: AdminService | None = None):
    """Render the standalone Backend Admin Portal."""
    configure_logging()
    _apply_admin_styles()
    admin_service = service or AdminService()

    if not st.session_state.get("admin_authenticated", False):
        _render_auth_gate(admin_service)
        return

    actor_email = st.session_state.get("admin_email", "admin")
    safe_actor = html.escape(str(actor_email))

    with st.sidebar:
        st.title("Admin Console")
        st.caption(f"Signed in as: `{actor_email}`")
        st.markdown("---")

        section = st.radio(
            "Navigation",
            [
                "Overview",
                "Resume Submissions",
                "AI Analytics",
                "User Feedback",
                "Registered Users",
                "Admin & Audit Logs",
            ],
            key="admin_portal_section",
        )

        st.markdown("---")
        overview = admin_service.get_system_overview()
        st.metric("Resumes", overview["total_resumes"])
        st.metric("AI Analyses", overview["ai_total_analyses"])
        st.metric("Storage (Resumes DB)", overview["resume_db_size"])

        st.markdown("---")
        if st.button("Logout", icon=":material/logout:", key="admin_portal_logout", width="stretch"):
            admin_service.log_admin_action(actor_email, "logout")
            st.session_state["admin_authenticated"] = False
            st.session_state["admin_email"] = None
            st.rerun()

    st.markdown(
        f"""
        <div class="admin-hero">
            <span class="admin-badge"><i class="fas fa-shield-alt"></i> BACKEND ADMIN PANEL</span>
            <h1>Resume Analyzer(AI) Administration</h1>
            <p>Authenticated administrator: <strong>{safe_actor}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if section == "Overview":
        _render_overview_tab(admin_service)
    elif section == "Resume Submissions":
        _render_resumes_tab(admin_service, actor_email)
    elif section == "AI Analytics":
        _render_ai_tab(admin_service, actor_email)
    elif section == "User Feedback":
        _render_feedback_tab(admin_service, actor_email)
    elif section == "Registered Users":
        _render_users_tab(admin_service, actor_email)
    elif section == "Admin & Audit Logs":
        _render_admin_accounts_tab(admin_service, actor_email)


def main():
    configure_page()
    render_admin_portal()


if __name__ == "__main__":
    main()
