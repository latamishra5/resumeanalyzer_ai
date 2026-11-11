"""Job search and LinkedIn scraper page views."""

import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_option_menu import option_menu

from backend.jobs.companies import get_featured_companies, get_market_insights
from backend.jobs.job_filters import filter_location_suggestions, get_filter_options
from backend.jobs.job_portals import JobPortal
from backend.jobs.linkedin_scraper import LinkedInScraperService
from backend.jobs.suggestions import JOB_SUGGESTIONS, LOCATION_SUGGESTIONS, get_cities_by_state


def _st_notifier(level, message):
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    else:
        st.info(message)


class LinkedInScraperUI:
    """Streamlit UI for LinkedIn job scraping."""

    @staticmethod
    def get_user_input(show_title=True):
        """Get user input for job search parameters"""
        add_vertical_space(1)

        if show_title:
            st.markdown("""
                <style>
                .linkedin-form {
                    background: rgba(10, 102, 194, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    border-left: 4px solid #0A66C2;
                    margin-bottom: 20px;
                }
                .linkedin-title {
                    color: #0A66C2;
                    font-weight: bold;
                }
                .linkedin-subtitle {
                    color: #666;
                    font-size: 0.9rem;
                    margin-bottom: 15px;
                }
                </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="linkedin-form">', unsafe_allow_html=True)
            st.markdown('<h3 class="linkedin-title"><i class="fab fa-linkedin"></i> LinkedIn Job Scraper</h3>', unsafe_allow_html=True)
            st.markdown('<p class="linkedin-subtitle">Find real-time job listings directly from LinkedIn</p>', unsafe_allow_html=True)

        with st.form(key='linkedin_scrape'):
            col1, col2, col3 = st.columns([0.5, 0.3, 0.2], gap='medium')

            with col1:
                job_title_input = st.text_input(
                    label='Job Title',
                    placeholder='e.g. Data Scientist, Software Engineer',
                    help="Enter job titles separated by commas",
                )
                job_title_input = job_title_input.split(',')

            with col2:
                job_location = st.text_input(
                    label='Job Location',
                    value='India',
                    placeholder='e.g. Bangalore, Mumbai, Remote',
                    help="Enter a location or 'India' for nationwide search",
                )

            with col3:
                job_count = st.number_input(
                    label='Number of Jobs',
                    min_value=1,
                    max_value=10,
                    value=3,
                    step=1,
                    help="Number of job listings to scrape (max 10)",
                )

            add_vertical_space(1)
            submit = st.form_submit_button(
                label='Search LinkedIn Jobs',
                type='primary',
                use_container_width=True,
            )
            add_vertical_space(1)

        if show_title:
            st.markdown('</div>', unsafe_allow_html=True)

        return job_title_input, job_location, job_count, submit

    @staticmethod
    def display_data_userinterface(df_final):
        """Display scraped job data in the user interface"""
        if df_final.empty:
            st.warning("No matching jobs found. Try different search terms or location.")
            return

        st.markdown("""
            <style>
            .job-card {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                border-left: 4px solid #0A66C2;
                transition: transform 0.2s;
            }
            .job-card:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            .job-title {
                color: #0A66C2;
                font-size: 1.3rem;
                margin-bottom: 0.5rem;
            }
            .company-name {
                font-weight: bold;
                font-size: 1.1rem;
            }
            .job-location {
                color: #888;
                margin-bottom: 1rem;
            }
            .job-url-button {
                display: inline-block;
                background: #0A66C2;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                text-decoration: none;
                margin-top: 1rem;
                font-weight: bold;
            }
            .job-url-button:hover {
                background: #084d8e;
            }
            .job-count {
                background: rgba(10, 102, 194, 0.1);
                color: #0A66C2;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                margin-bottom: 1rem;
                font-weight: bold;
            }
            .job-section {
                margin-top: 1rem;
                padding-top: 0.5rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .job-section-title {
                font-weight: bold;
                color: #0A66C2;
                margin-bottom: 0.5rem;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="job-count">🎯 Found {len(df_final)} matching jobs on LinkedIn</div>', unsafe_allow_html=True)

        for i in range(len(df_final)):
            company_name = df_final.iloc[i, 0]
            job_title = df_final.iloc[i, 1]
            location = df_final.iloc[i, 2]
            url = df_final.iloc[i, 3]
            description = df_final.iloc[i, 4]

            st.markdown(f"""
                <div class="job-card">
                    <div class="job-title">{job_title}</div>
                    <div class="company-name">{company_name}</div>
                    <div class="job-location">📍 {location}</div>
                </div>
            """, unsafe_allow_html=True)

            with st.expander("View Job Description"):
                st.markdown(description)
                st.markdown(f"<a href='{url}' target='_blank' class='job-url-button'>Apply on LinkedIn</a>", unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

    @staticmethod
    def main(show_title=True):
        """Main UI flow for LinkedIn job scraper"""
        driver = None

        try:
            job_title_input, job_location, job_count, submit = LinkedInScraperUI.get_user_input(show_title)

            if submit:
                if job_title_input != [''] and job_location:
                    try:
                        with st.spinner('Setting up Chrome webdriver...'):
                            driver = LinkedInScraperService.webdriver_setup(on_status=_st_notifier)
                            if not driver:
                                st.error("Failed to initialize Chrome webdriver. Please make sure Chrome is installed.")
                                return

                        with st.spinner('Loading LinkedIn jobs page...'):
                            link = LinkedInScraperService.build_url(job_title_input, job_location)
                            st.info(f"Searching for: {', '.join([t for t in job_title_input if t.strip()])} in {job_location}")
                            success = LinkedInScraperService.link_open_scrolldown(
                                driver, link, job_count, on_status=_st_notifier
                            )
                            if not success:
                                st.error("Failed to load LinkedIn jobs page. Please try again.")
                                return

                        with st.spinner('Scraping job listings...'):
                            df = LinkedInScraperService.scrap_company_data(
                                driver, job_title_input, job_location, on_status=_st_notifier
                            )
                            if df.empty:
                                st.warning("No jobs found matching your criteria. Try different search terms.")
                                return

                        with st.spinner('Fetching job descriptions...'):
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            def _update_progress(pct, text):
                                progress_bar.progress(pct)
                                status_text.text(text)

                            df_final = LinkedInScraperService.scrap_job_description(
                                driver,
                                df,
                                job_count,
                                on_status=_st_notifier,
                                on_progress=_update_progress,
                            )
                            progress_bar.empty()
                            status_text.empty()

                            if df_final.empty:
                                st.warning("Could not retrieve job descriptions. Try different search terms.")
                                return

                        LinkedInScraperUI.display_data_userinterface(df_final)

                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")
                        st.info("Try refreshing the page or using different search terms.")

                elif job_title_input == ['']:
                    st.warning("Please enter a job title to search.")

                elif not job_location:
                    st.warning("Please enter a job location to search.")

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

        finally:
            if driver:
                driver.quit()


def render_linkedin_scraper():
    """Render the LinkedIn job scraper interface"""
    LinkedInScraperUI.main(show_title=False)


def render_company_section():
    """Render the featured companies section"""
    st.markdown("""
        <style>
        .company-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
            padding: 1rem 0;
        }
        .company-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1rem;
            transition: transform 0.2s;
            cursor: pointer;
        }
        .company-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.08);
        }
        .company-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .company-icon {
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }
        .company-categories {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        .company-category {
            background: rgba(255, 255, 255, 0.1);
            padding: 0.2rem 0.5rem;
            border-radius: 15px;
            font-size: 0.8rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🏢 Featured Companies")

    tabs = st.tabs(["All Companies", "Tech Giants", "Indian Tech", "Global Corps"])

    categories = [None, "tech", "indian_tech", "global_corps"]
    for tab, category in zip(tabs, categories):
        with tab:
            companies = get_featured_companies(category)
            st.markdown('<div class="company-grid">', unsafe_allow_html=True)

            for company in companies:
                st.markdown(f"""
                    <a href="{company['careers_url']}" target="_blank" style="text-decoration: none; color: inherit;">
                        <div class="company-card">
                            <div class="company-header">
                                <i class="{company['icon']} company-icon" style="color: {company['color']}"></i>
                                <h3 style="margin: 0;">{company['name']}</h3>
                            </div>
                            <p style="margin: 0.5rem 0; color: #888;">{company['description']}</p>
                            <div class="company-categories">
                                {' '.join(f'<span class="company-category">{cat}</span>' for cat in company['categories'])}
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)


def render_market_insights():
    """Render job market insights section"""
    insights = get_market_insights()

    st.markdown("""
        <style>
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            padding: 1rem 0;
        }
        .insight-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            transition: transform 0.3s ease, background 0.3s ease;
        }
        .insight-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.08);
        }
        .insight-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: #00bfa5;
        }
        .growth-text {
            color: #00c853;
            font-weight: bold;
        }
        .salary-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            border-left: 4px solid #00bfa5;
        }
        .salary-card:hover {
            transform: translateX(10px);
            background: rgba(255, 255, 255, 0.08);
        }
        .salary-header {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .role-icon {
            font-size: 1.5rem;
            margin-right: 1rem;
            color: #00bfa5;
        }
        .salary-details {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 0.5rem;
        }
        .salary-tag {
            background: rgba(0, 191, 165, 0.1);
            color: #00bfa5;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .experience-tag {
            background: rgba(255, 255, 255, 0.1);
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .role-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin: 0;
        }
        .salary-range {
            font-size: 1.1rem;
            color: #00bfa5;
            font-weight: bold;
        }
        .role-icons {
            font-family: "Font Awesome 5 Free";
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Job Market Insights")

    tabs = st.tabs(["Trending Skills", "Top Locations", "Salary Insights"])

    with tabs[0]:
        st.markdown('<div class="insights-grid">', unsafe_allow_html=True)
        for skill in insights["trending_skills"]:
            st.markdown(f"""
                <div class="insight-card">
                    <i class="{skill['icon']} insight-icon"></i>
                    <h4>{skill['name']}</h4>
                    <p class="growth-text">Growth: {skill['growth']}</p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="insights-grid">', unsafe_allow_html=True)
        for location in insights["top_locations"]:
            st.markdown(f"""
                <div class="insight-card">
                    <i class="{location['icon']} insight-icon"></i>
                    <h4>{location['name']}</h4>
                    <p>Available Jobs: {location['jobs']}</p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        role_icons = {
            "Software Engineer": "fas fa-code",
            "Data Scientist": "fas fa-brain",
            "Product Manager": "fas fa-tasks",
            "DevOps Engineer": "fas fa-server",
            "UI/UX Designer": "fas fa-paint-brush",
        }

        for insight in insights["salary_insights"]:
            role = insight['role']
            icon = role_icons.get(role, "fas fa-briefcase")

            st.markdown(f"""
                <div class="salary-card">
                    <div class="salary-header">
                        <i class="{icon} role-icon"></i>
                        <div>
                            <h3 class="role-title">{role}</h3>
                            <div class="salary-details">
                                <span class="salary-tag">₹ {insight['range']}</span>
                                <span class="experience-tag">
                                    <i class="fas fa-history"></i> {insight['experience']}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_job_search():
    """Render job search page with enhanced features"""
    st.title("🔍 Smart Job Search")
    st.markdown("Find Your Dream Job Across Multiple Platforms")

    render_market_insights()

    with st.container():
        st.markdown("""
            <style>
            .search-container {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .search-title {
                color: #00bfa5;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .search-description {
                color: #888;
                font-size: 0.9rem;
                margin-bottom: 20px;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="search-container">', unsafe_allow_html=True)

        tabs = option_menu(
            menu_title=None,
            options=["Job Portal", "LinkedIn"],
            icons=["search", "linkedin"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0px", "margin-bottom": "20px"},
                "icon": {"font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "center", "padding": "10px", "border-radius": "5px"},
                "nav-link-selected": {"background-color": "#00bfa5", "font-weight": "bold"},
            },
        )

        if tabs == "Job Portal":
            st.markdown('<h3 class="search-title"><i class="fas fa-search-dollar" style="color: #00bfa5;"></i> Search Jobs Across Multiple Platforms</h3>', unsafe_allow_html=True)
            st.markdown('<p class="search-description">Find job opportunities from top job portals like LinkedIn, Indeed, Naukri, and Foundit</p>', unsafe_allow_html=True)

            col1, col2 = st.columns([2, 1])

            with col1:
                job_query = st.text_input(
                    "Job Title / Skills",
                    value="",
                    placeholder="e.g. Software Engineer, Data Scientist",
                )

                if job_query and len(job_query) >= 2:
                    filtered_jobs = [s["text"] for s in JOB_SUGGESTIONS if job_query.lower() in s["text"].lower()]
                    if filtered_jobs:
                        job_query = st.selectbox("Select Job Title", filtered_jobs)

            with col2:
                location = st.text_input(
                    "Location",
                    value="",
                    placeholder="e.g. Bangalore, Karnataka",
                )

                if location and len(location) >= 2:
                    filtered_locations = filter_location_suggestions(location, LOCATION_SUGGESTIONS)

                    if filtered_locations:
                        location_options = []
                        location_display = {}

                        for loc in filtered_locations:
                            display_text = loc["text"]
                            if loc.get("type") == "state":
                                display_text = f"{loc['text']} (State)"
                            elif loc.get("type") == "city":
                                display_text = f"{loc['text']}, {loc.get('state', '')}"
                            elif loc.get("type") == "work_mode":
                                display_text = f"{loc['text']} (Work Mode)"

                            location_options.append(loc["text"])
                            location_display[loc["text"]] = display_text

                        selected_location = st.selectbox(
                            "Select Location",
                            options=location_options,
                            format_func=lambda x: location_display.get(x, x),
                        )

                        location = selected_location

                        selected_loc_type = next(
                            (loc.get("type") for loc in filtered_locations if loc["text"] == selected_location),
                            None,
                        )

                        if selected_loc_type == "state":
                            st.markdown(f"**Cities in {selected_location}:**")
                            cities = get_cities_by_state(selected_location)

                            city_cols = st.columns(3)
                            for i, city in enumerate(cities):
                                with city_cols[i % 3]:
                                    if st.button(f"{city['icon']} {city['text']}", key=f"city_{i}"):
                                        location = city['text']

            with st.expander("🎯 Advanced Filters"):
                st.markdown('<div class="filter-section">', unsafe_allow_html=True)
                filter_cols = st.columns(3)

                with filter_cols[0]:
                    experience = st.selectbox(
                        "Experience Level",
                        options=get_filter_options()["experience_levels"],
                        format_func=lambda x: x["text"],
                    )

                with filter_cols[1]:
                    _salary_range = st.selectbox(
                        "Salary Range",
                        options=get_filter_options()["salary_ranges"],
                        format_func=lambda x: x["text"],
                    )

                with filter_cols[2]:
                    _job_type = st.selectbox(
                        "Job Type",
                        options=get_filter_options()["job_types"],
                        format_func=lambda x: x["text"],
                    )

                st.markdown('</div>', unsafe_allow_html=True)

            if st.button("SEARCH JOBS", type="primary", use_container_width=True):
                if job_query:
                    job_portal = JobPortal()
                    results = job_portal.search_jobs(job_query, location, experience)

                    if results:
                        st.markdown("""
                            <style>
                            .result-card {
                                background: rgba(255, 255, 255, 0.05);
                                border-radius: 10px;
                                padding: 15px;
                                margin-bottom: 10px;
                                border-left: 4px solid #00bfa5;
                                transition: transform 0.2s;
                            }
                            .result-card:hover {
                                transform: translateX(5px);
                                background: rgba(255, 255, 255, 0.08);
                            }
                            .portal-name {
                                color: #00bfa5;
                                font-weight: bold;
                                font-size: 1.2rem;
                            }
                            .portal-link {
                                display: inline-block;
                                background: #00bfa5;
                                color: white !important;
                                padding: 5px 15px;
                                border-radius: 5px;
                                text-decoration: none;
                                margin-top: 10px;
                                font-weight: bold;
                            }
                            .portal-link:hover {
                                background: #00a589;
                            }
                            </style>
                        """, unsafe_allow_html=True)

                        st.markdown("### 🎯 Job Search Results")
                        for result in results:
                            with st.container():
                                st.markdown(f"""
                                <div class="result-card">
                                    <div class="portal-name">
                                        <i class="{result["icon"]}" style="color: {result["color"]}"></i>
                                        {result["portal"]}
                                    </div>
                                    <p>{result["title"]}</p>
                                    <a href="{result["url"]}" target="_blank" class="portal-link">
                                        View Jobs on {result["portal"]} →
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("No results found. Try different search terms or filters.")
                else:
                    st.warning("Please enter a job title or skills to search.")

        else:
            st.markdown('<h3 class="search-title"><i class="fab fa-linkedin" style="color: #0A66C2;"></i> LinkedIn Job Scraper</h3>', unsafe_allow_html=True)
            st.markdown('<p class="search-description">Find real-time job listings directly from LinkedIn</p>', unsafe_allow_html=True)
            render_linkedin_scraper()

        st.markdown('</div>', unsafe_allow_html=True)

    render_company_section()


def render_job_search_page():
    """Render the job search page with page toast."""
    render_job_search()
    st.toast("Check out these repositories: [GeeksforGeeks-POTD](https://github.com/latamishra5/GeeksforGeeks-POTD)", icon="ℹ️")
