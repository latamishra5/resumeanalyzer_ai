"""Dashboard page view and Plotly visualization manager."""

from datetime import datetime
from io import BytesIO
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.services.dashboard_service import DashboardService


class DashboardManager:
    def __init__(self, service=None):
        self.service = service or DashboardService()
        self.colors = {
            'primary': '#4CAF50',
            'secondary': '#2196F3',
            'warning': '#FFA726',
            'danger': '#F44336',
            'info': '#00BCD4',
            'success': '#66BB6A',
            'purple': '#9C27B0',
            'background': '#1E1E1E',
            'card': '#2D2D2D',
            'text': '#FFFFFF',
            'subtext': '#B0B0B0',
        }

    def apply_dashboard_style(self):
        """Apply custom styling for dashboard"""
        st.markdown("""
            <style>
                .dashboard-title {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin-bottom: 2rem;
                    color: white;
                    text-align: center;
                }

                .metric-card {
                    background-color: #2D2D2D;
                    border-radius: 15px;
                    padding: 1.5rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease;
                    height: 100%;
                }

                .metric-card:hover {
                    transform: translateY(-5px);
                }

                .metric-value {
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: #4CAF50;
                    margin: 0.5rem 0;
                }

                .metric-label {
                    font-size: 1rem;
                    color: #B0B0B0;
                }

                .trend-up {
                    color: #4CAF50;
                    font-size: 1.2rem;
                }

                .trend-down {
                    color: #F44336;
                    font-size: 1.2rem;
                }

                .chart-container {
                    background-color: #2D2D2D;
                    border-radius: 15px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                }

                .section-title {
                    font-size: 1.5rem;
                    color: white;
                    margin: 2rem 0 1rem 0;
                }

                .stPlotlyChart {
                    background-color: #2D2D2D;
                    border-radius: 15px;
                    padding: 1rem;
                }

                div[data-testid="stHorizontalBlock"] > div {
                    background-color: #2D2D2D;
                    border-radius: 15px;
                    padding: 1rem;
                    margin: 0.5rem;
                }

                [data-testid="stMetricValue"] {
                    font-size: 2rem !important;
                }

                [data-testid="stMetricLabel"] {
                    font-size: 1rem !important;
                }
            </style>
        """, unsafe_allow_html=True)

    def get_resume_metrics(self):
        return self.service.get_resume_metrics()

    def get_skill_distribution(self):
        return self.service.get_skill_distribution()

    def get_weekly_trends(self):
        return self.service.get_weekly_trends()

    def get_job_category_stats(self):
        return self.service.get_job_category_stats()

    def get_resume_data(self):
        return self.service.get_resume_data()

    def get_database_stats(self):
        return self.service.get_database_stats()

    def get_admin_logs(self):
        return self.service.get_admin_logs()

    def get_trend_indicators(self):
        return self.service.get_trend_indicators()

    def get_detailed_insights(self):
        return self.service.get_detailed_insights()

    def get_quick_stats(self):
        return self.service.get_quick_stats()

    def export_to_excel(self):
        try:
            return self.service.export_to_excel()
        except Exception as e:
            st.error(f"Error exporting to Excel: {str(e)}")
            return None

    def export_to_csv(self):
        try:
            return self.service.export_to_csv()
        except Exception as e:
            st.error(f"Error exporting to CSV: {str(e)}")
            return None

    def export_to_json(self):
        try:
            return self.service.export_to_json()
        except Exception as e:
            st.error(f"Error exporting to JSON: {str(e)}")
            return None

    def render_admin_panel(self):
        """Render admin panel with data management tools"""
        st.sidebar.markdown("### 👋 Welcome Admin!")
        st.sidebar.markdown("---")

        if st.sidebar.button("🚪 Logout"):
            st.session_state.is_admin = False
            st.rerun()

        st.sidebar.markdown("### 🛠️ Admin Tools")

        export_format = st.sidebar.selectbox(
            "Export Format",
            ["Excel", "CSV", "JSON"],
            key="export_format",
        )

        if st.sidebar.button("📥 Export Data"):
            if export_format == "Excel":
                excel_data = self.export_to_excel()
                if excel_data:
                    st.sidebar.download_button(
                        "⬇️ Download Excel",
                        data=excel_data,
                        file_name=f"resume_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            elif export_format == "CSV":
                csv_data = self.export_to_csv()
                if csv_data:
                    st.sidebar.download_button(
                        "⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"resume_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                    )
            else:
                json_data = self.export_to_json()
                if json_data:
                    st.sidebar.download_button(
                        "⬇️ Download JSON",
                        data=json_data,
                        file_name=f"resume_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                    )

        st.sidebar.markdown("### 📊 Database Stats")
        stats = self.get_database_stats()
        st.sidebar.markdown(f"""
            - Total Resumes: {stats['total_resumes']}
            - Today's Submissions: {stats['today_submissions']}
            - Storage Used: {stats['storage_size']}
        """)

    def render_resume_data_section(self):
        """Render resume data section with Excel download"""
        st.markdown("<h2 class='section-title'>Resume Submissions</h2>", unsafe_allow_html=True)

        resume_data = self.get_resume_data()

        if resume_data:
            columns = [
                'ID', 'Name', 'Email', 'Phone', 'LinkedIn', 'GitHub',
                'Portfolio', 'Target Role', 'Target Category', 'Submission Date',
                'ATS Score', 'Keyword Match', 'Format Score', 'Section Score',
            ]
            df = pd.DataFrame(resume_data, columns=columns)

            score_columns = ['ATS Score', 'Keyword Match', 'Format Score', 'Section Score']
            for col in score_columns:
                df[col] = df[col].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "N/A")

            st.markdown("""
            <style>
            .resume-data {
                background-color: #2D2D2D;
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
            }
            </style>
            """, unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="resume-data">', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    target_role = st.selectbox(
                        "Filter by Target Role",
                        options=["All"] + list(df['Target Role'].unique()),
                        key="role_filter",
                    )
                with col2:
                    target_category = st.selectbox(
                        "Filter by Category",
                        options=["All"] + list(df['Target Category'].unique()),
                        key="category_filter",
                    )

                filtered_df = df.copy()
                if target_role != "All":
                    filtered_df = filtered_df[filtered_df['Target Role'] == target_role]
                if target_category != "All":
                    filtered_df = filtered_df[filtered_df['Target Category'] == target_category]

                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                )

                col1, col2 = st.columns(2)
                with col1:
                    excel_buffer = BytesIO()
                    filtered_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_buffer.seek(0)

                    st.download_button(
                        label="📥 Download Filtered Data",
                        data=excel_buffer,
                        file_name=f"resume_data_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_filtered_data",
                    )

                with col2:
                    excel_buffer_all = BytesIO()
                    df.to_excel(excel_buffer_all, index=False, engine='openpyxl')
                    excel_buffer_all.seek(0)

                    st.download_button(
                        label="📥 Download All Data",
                        data=excel_buffer_all,
                        file_name=f"resume_data_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="download_all_data",
                    )

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No resume submissions available")

    def render_admin_section(self):
        """Render admin section with logs and Excel download"""
        self.render_resume_data_section()

        st.markdown("<h2 class='section-title'>Admin Activity Logs</h2>", unsafe_allow_html=True)

        admin_logs = self.get_admin_logs()

        if admin_logs:
            df = pd.DataFrame(admin_logs, columns=['Admin Email', 'Action', 'Timestamp'])

            st.markdown("""
            <style>
            .admin-logs {
                background-color: #2D2D2D;
                border-radius: 10px;
                padding: 1rem;
            }
            </style>
            """, unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="admin-logs">', unsafe_allow_html=True)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )

                excel_buffer = BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)

                st.download_button(
                    label="📥 Download Admin Logs as Excel",
                    data=excel_buffer,
                    file_name=f"admin_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_admin_logs",
                )
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No admin activity logs available")

    def render_dashboard(self):
        """Main dashboard rendering function"""
        st.markdown("""
            <style>
                .dashboard-container {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 2rem;
                    border-radius: 20px;
                    margin: -1rem -1rem 2rem -1rem;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                .dashboard-title {
                    color: #4FD1C5;
                    font-size: 2.5rem;
                    margin-bottom: 0.5rem;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                }
                .dashboard-icon {
                    background: rgba(79, 209, 197, 0.2);
                    padding: 0.5rem;
                    border-radius: 12px;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 1.5rem;
                    margin-top: 2rem;
                }
                .stat-card {
                    background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    padding: 1.5rem;
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    transition: all 0.3s ease;
                }
                .stat-card:hover {
                    transform: translateY(-5px);
                    background: rgba(255, 255, 255, 0.1);
                }
                .stat-value {
                    font-size: 2.5rem;
                    font-weight: bold;
                    margin: 0;
                    color: #4FD1C5;
                }
                .stat-label {
                    font-size: 1rem;
                    color: rgba(255, 255, 255, 0.7);
                    margin: 0.5rem 0 0 0;
                }
                .section-title {
                    color: #4FD1C5;
                    font-size: 1.5rem;
                    margin: 1rem 0 0.5rem 0;
                    padding-bottom: 0.5rem;
                    border-bottom: 2px solid rgba(79, 209, 197, 0.2);
                }
                .chart-container {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 16px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                }
                .insights-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 1.5rem;
                    margin-top: 1rem;
                }
                .insight-card {
                    background: rgba(255, 255, 255, 0.05);
                    padding: 1.5rem;
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                .trend-indicator {
                    display: inline-flex;
                    align-items: center;
                    padding: 0.25rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.875rem;
                    margin-left: 0.5rem;
                }
                .trend-up {
                    background: rgba(46, 204, 113, 0.2);
                    color: #2ecc71;
                }
                .trend-down {
                    background: rgba(231, 76, 60, 0.2);
                    color: #e74c3c;
                }
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .animate-fade-in {
                    animation: fadeInUp 0.5s ease-out forwards;
                }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="dashboard-container animate-fade-in">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div class="dashboard-title">
                        <span class="dashboard-icon">📊</span>
                        Resume Analytics Dashboard
                    </div>
                    <div style="color: rgba(255, 255, 255, 0.7);">
                        Last updated: {}
                    </div>
                </div>
            """.format(datetime.now().strftime('%B %d, %Y %I:%M %p')), unsafe_allow_html=True)

        stats = self.get_quick_stats()
        trend_indicators = self.get_trend_indicators()

        st.markdown("""
            <div class="stats-grid">
                <div class="stat-card">
                    <p class="stat-value">{}</p>
                    <p class="stat-label">Total Resumes</p>
                    <span class="trend-indicator {}">
                        {} {}%
                    </span>
                </div>
                <div class="stat-card">
                    <p class="stat-value">{}</p>
                    <p class="stat-label">Avg ATS Score</p>
                    <span class="trend-indicator {}">
                        {} {}%
                    </span>
                </div>
                <div class="stat-card">
                    <p class="stat-value">{}</p>
                    <p class="stat-label">High Performing</p>
                    <span class="trend-indicator {}">
                        {} {}%
                    </span>
                </div>
                <div class="stat-card">
                    <p class="stat-value">{}</p>
                    <p class="stat-label">Success Rate</p>
                    <span class="trend-indicator {}">
                        {} {}%
                    </span>
                </div>
            </div>
            </div>
        """.format(
            stats['Total Resumes'],
            trend_indicators['resumes']['class'], trend_indicators['resumes']['icon'], trend_indicators['resumes']['value'],
            stats['Avg ATS Score'],
            trend_indicators['ats']['class'], trend_indicators['ats']['icon'], trend_indicators['ats']['value'],
            stats['High Performing'],
            trend_indicators['high_performing']['class'], trend_indicators['high_performing']['icon'], trend_indicators['high_performing']['value'],
            stats['Success Rate'],
            trend_indicators['success_rate']['class'], trend_indicators['success_rate']['icon'], trend_indicators['success_rate']['value'],
        ), unsafe_allow_html=True)

        st.markdown('<div class="section-title">📈 Performance Analytics</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = self.create_enhanced_ats_gauge(float(stats['Avg ATS Score'].rstrip('%')))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = self.create_skill_distribution_chart()
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = self.create_submission_trends_chart()
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            fig = self.create_job_category_chart()
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">🎯 Key Insights</div>', unsafe_allow_html=True)
        insights = self.get_detailed_insights()

        st.markdown('<div class="insights-grid">', unsafe_allow_html=True)
        for insight in insights:
            st.markdown(f"""
                <div class="insight-card">
                    <h3 style="color: #4FD1C5; margin-bottom: 1rem;">
                        {insight['icon']} {insight['title']}
                    </h3>
                    <p style="color: rgba(255, 255, 255, 0.7); margin: 0;">
                        {insight['description']}
                    </p>
                    <div style="margin-top: 1rem;">
                        <span class="trend-indicator {insight['trend_class']}">
                            {insight['trend_icon']} {insight['trend_value']}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.get('is_admin', False):
            self.render_admin_section()

    def create_enhanced_ats_gauge(self, value):
        """Create an enhanced ATS score gauge chart"""
        reference = 70

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            delta={
                'reference': reference,
                'valueformat': '.1f',
                'increasing': {'color': '#2ecc71'},
                'decreasing': {'color': '#e74c3c'},
            },
            number={'font': {'size': 40, 'color': 'white'}},
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickwidth': 1,
                    'tickcolor': 'white',
                    'tickfont': {'color': 'white'},
                },
                'bar': {'color': '#3498db'},
                'bgcolor': 'rgba(0,0,0,0)',
                'borderwidth': 2,
                'bordercolor': 'white',
                'steps': [
                    {'range': [0, 40], 'color': '#e74c3c'},
                    {'range': [40, 70], 'color': '#f1c40f'},
                    {'range': [70, 100], 'color': '#2ecc71'},
                ],
                'threshold': {
                    'line': {'color': 'white', 'width': 4},
                    'thickness': 0.75,
                    'value': reference,
                },
            },
        ))

        fig.update_layout(
            title={
                'text': 'ATS Score Performance',
                'font': {'size': 24, 'color': 'white'},
                'y': 0.85,
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': 'white'},
            height=350,
            margin=dict(l=20, r=20, t=80, b=20),
        )

        return fig

    def create_skill_distribution_chart(self):
        """Create a skill distribution chart"""
        categories, counts = self.get_skill_distribution()

        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=counts,
                marker_color=self.colors['info'],
                text=counts,
                textposition='auto',
            )
        ])

        fig.update_layout(
            title={
                'text': 'Skill Distribution',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
            },
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=self.colors['text']),
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='rgba(255,255,255,0.2)',
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                zeroline=False,
            ),
            bargap=0.3,
        )
        return fig

    def create_submission_trends_chart(self):
        """Create a weekly submission trend chart"""
        dates, submissions = self.get_weekly_trends()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=submissions,
            mode='lines+markers',
            line=dict(color=self.colors['info'], width=3),
            marker=dict(size=8, color=self.colors['info']),
        ))

        fig.update_layout(
            title="Weekly Submission Pattern",
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        fig.update_xaxes(title_text="Day of Week", color=self.colors['text'])
        fig.update_yaxes(title_text="Number of Submissions", color=self.colors['text'])

        return fig

    def create_job_category_chart(self):
        """Create a success rate by category chart"""
        categories, rates = self.get_job_category_stats()
        fig = go.Figure(go.Bar(
            x=categories,
            y=rates,
            marker_color=[
                self.colors['success'], self.colors['info'],
                self.colors['warning'], self.colors['purple'],
                self.colors['secondary'],
            ],
            text=[f"{rate}%" for rate in rates],
            textposition='auto',
        ))

        fig.update_layout(
            title="Success Rate by Job Category",
            paper_bgcolor=self.colors['card'],
            plot_bgcolor=self.colors['card'],
            font={'color': self.colors['text']},
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        fig.update_xaxes(title_text="Job Category", color=self.colors['text'])
        fig.update_yaxes(title_text="Success Rate (%)", color=self.colors['text'])

        return fig


def render_dashboard(dashboard_manager=None):
    """Render the dashboard page"""
    manager = dashboard_manager or DashboardManager()
    manager.render_dashboard()
    st.toast("Check out these repositories: [Awesome Hacking](https://github.com/latamishra5/Awesome-Hacking)", icon="ℹ️")
