"""Pure Python LinkedIn scraping service (UI-agnostic)."""

import logging
import time
import warnings

import numpy as np
import pandas as pd
from selenium.webdriver.common.by import By

from .webdriver_utils import setup_webdriver

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class LinkedInScraperService:
    """Service for scraping job listings from LinkedIn."""

    @staticmethod
    def _notify(on_status, level, message):
        if on_status is not None:
            on_status(level, message)
        elif level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

    @staticmethod
    def webdriver_setup(on_status=None):
        """Set up and configure the Chrome webdriver"""
        return setup_webdriver(on_status=on_status)

    @staticmethod
    def build_url(job_title, job_location):
        """Build LinkedIn search URL from job title and location"""
        formatted_titles = []
        for title in job_title:
            if title.strip():
                words = title.strip().split()
                formatted_title = '%20'.join(words)
                formatted_titles.append(formatted_title)

        if not formatted_titles:
            formatted_titles = ["jobs"]

        job_title_param = '%2C%20'.join(formatted_titles)
        location_param = job_location.replace(' ', '%20')
        return (
            f"https://in.linkedin.com/jobs/search?keywords={job_title_param}"
            f"&location={location_param}&geoId=102713980&f_TPR=r604800&position=1&pageNum=0"
        )

    @staticmethod
    def open_link(driver, link, on_status=None):
        """Open LinkedIn link and wait for page to load"""
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            try:
                driver.get(link)
                driver.implicitly_wait(5)
                time.sleep(3)

                if "LinkedIn" in driver.title:
                    return True

                for selector in ('.jobs-search-results', '.jobs-search-results-list', '.base-search-card'):
                    try:
                        driver.find_element(by=By.CSS_SELECTOR, value=selector)
                        return True
                    except Exception:
                        pass

                attempts += 1
                if attempts >= max_attempts:
                    LinkedInScraperService._notify(
                        on_status, "warning", "Could not load LinkedIn jobs page. Please try again."
                    )
                    return False

                time.sleep(2)

            except Exception as e:
                attempts += 1
                if attempts >= max_attempts:
                    LinkedInScraperService._notify(
                        on_status, "warning", f"Error loading LinkedIn page: {str(e)}"
                    )
                    return False
                time.sleep(2)

        return False

    @staticmethod
    def link_open_scrolldown(driver, link, job_count, on_status=None):
        """Open LinkedIn link and scroll down to load more jobs"""
        if not LinkedInScraperService.open_link(driver, link, on_status=on_status):
            return False

        scroll_attempts = min(job_count + 5, 15)

        for _ in range(scroll_attempts):
            try:
                try:
                    dismiss_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR,
                        value="button[data-tracking-control-name='public_jobs_contextual-sign-in-modal_modal_dismiss']",
                    )
                    if dismiss_buttons:
                        dismiss_buttons[0].click()
                except Exception:
                    pass

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)

                try:
                    see_more_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR,
                        value="button[aria-label='See more jobs']",
                    )
                    if see_more_buttons:
                        see_more_buttons[0].click()
                        time.sleep(2)
                except Exception:
                    pass

            except Exception:
                continue

        return True

    @staticmethod
    def job_title_filter(scrap_job_title, user_job_title_input):
        """Filter job titles based on user input"""
        if not user_job_title_input or all(not title.strip() for title in user_job_title_input):
            return scrap_job_title

        user_input = [title.lower().strip() for title in user_job_title_input if title.strip()]
        if not user_input:
            return scrap_job_title

        scrap_title = scrap_job_title.lower().strip()
        for user_title in user_input:
            if all(word in scrap_title for word in user_title.split()):
                return scrap_job_title

        return np.nan

    @staticmethod
    def scrap_company_data(driver, job_title_input, job_location, on_status=None):
        """Scrape company data from LinkedIn job listings"""
        try:
            company_elements = driver.find_elements(by=By.CSS_SELECTOR, value='h4.base-search-card__subtitle')
            company_names = [element.text for element in company_elements if element.text.strip()]

            location_elements = driver.find_elements(by=By.CSS_SELECTOR, value='span.job-search-card__location')
            company_locations = [element.text for element in location_elements if element.text.strip()]

            title_elements = driver.find_elements(by=By.CSS_SELECTOR, value='h3.base-search-card__title')
            job_titles = [element.text for element in title_elements if element.text.strip()]

            url_elements = driver.find_elements(by=By.XPATH, value='//a[contains(@href, "/jobs/view/")]')
            job_urls = [element.get_attribute('href') for element in url_elements if element.get_attribute('href')]

            if not company_names or not job_titles or not company_locations or not job_urls:
                LinkedInScraperService._notify(
                    on_status, "warning", "No job listings found on LinkedIn. Try different search terms."
                )
                return pd.DataFrame()

            min_length = min(len(company_names), len(job_titles), len(company_locations), len(job_urls))
            if min_length == 0:
                LinkedInScraperService._notify(
                    on_status, "warning", "No job listings found on LinkedIn. Try different search terms."
                )
                return pd.DataFrame()

            df = pd.DataFrame({
                'Company Name': company_names[:min_length],
                'Job Title': job_titles[:min_length],
                'Location': company_locations[:min_length],
                'Website URL': job_urls[:min_length],
            })

            if job_title_input and job_title_input != ['']:
                filtered_titles = []
                for title in df['Job Title']:
                    if any(user_title.lower().strip() in title.lower() for user_title in job_title_input if user_title.strip()):
                        filtered_titles.append(title)
                    else:
                        filtered_titles.append(np.nan)
                df['Job Title'] = filtered_titles

            if job_location and job_location.lower() != "india":
                filtered_locations = []
                for loc in df['Location']:
                    if job_location.lower() in loc.lower():
                        filtered_locations.append(loc)
                    else:
                        filtered_locations.append(np.nan)
                df['Location'] = filtered_locations

            df = df.dropna()
            df = df.reset_index(drop=True)
            return df

        except Exception as e:
            LinkedInScraperService._notify(on_status, "error", f"Error scraping company data: {str(e)}")
            LinkedInScraperService._notify(on_status, "info", "Try refreshing the page or using different search terms.")
            return pd.DataFrame()

    @staticmethod
    def scrap_job_description(driver, df, job_count, on_status=None, on_progress=None):
        """Scrape job descriptions for each job listing"""
        if df.empty:
            return df

        job_urls = df['Website URL'].tolist()[:min(len(df), job_count)]
        job_descriptions = []

        for i, url in enumerate(job_urls):
            try:
                progress = int((i + 1) / len(job_urls) * 100)
                if on_progress is not None:
                    on_progress(progress, f"Scraping job {i+1} of {len(job_urls)}...")

                driver.get(url)
                driver.implicitly_wait(5)
                time.sleep(2)

                try:
                    show_more_buttons = driver.find_elements(
                        by=By.CSS_SELECTOR,
                        value='button[data-tracking-control-name="public_jobs_show-more-html-btn"]',
                    )
                    if show_more_buttons:
                        show_more_buttons[0].click()
                        time.sleep(1)
                except Exception:
                    pass

                description_elements = driver.find_elements(
                    by=By.CSS_SELECTOR,
                    value='div.show-more-less-html__markup',
                )

                if description_elements and description_elements[0].text.strip():
                    description_text = description_elements[0].text
                    job_descriptions.append(LinkedInScraperService.process_job_description(description_text))
                else:
                    alt_description = driver.find_elements(by=By.CSS_SELECTOR, value='div.description__text')
                    if alt_description and alt_description[0].text.strip():
                        description_text = alt_description[0].text
                        job_descriptions.append(LinkedInScraperService.process_job_description(description_text))
                    else:
                        job_descriptions.append("Description not available")

            except Exception as e:
                job_descriptions.append("Description not available")
                LinkedInScraperService._notify(
                    on_status, "warning", f"Error scraping job description {i+1}: {str(e)}"
                )

        df = df.iloc[:len(job_descriptions), :].copy()
        df['Job Description'] = job_descriptions
        df['Job Description'] = df['Job Description'].apply(
            lambda x: np.nan if x == "Description not available" else x
        )
        df = df.dropna()
        df = df.reset_index(drop=True)
        return df

    @staticmethod
    def process_job_description(text):
        """Process and structure job description text"""
        if not text or text == "Description not available":
            return text

        sections = text.split('\n\n')
        processed_sections = []

        section_headers = [
            "responsibilities", "requirements", "qualifications", "skills",
            "about the job", "about the role", "what you'll do", "what you'll need",
            "about us", "about the company", "who we are", "benefits", "perks",
            "job description", "role description", "experience", "education",
            "job summary", "job overview", "job requirements", "job responsibilities",
            "job qualifications", "job skills", "job benefits", "job perks",
            "Education Qualification and Experience", "Required Skills", "Preferred Qualifications", "Key Responsibilities",
            "About Us", "About the Company", "About the Role", "About the Job",
            "About the Team", "About the Organization", "About the Industry", "About the Location",
            "Position", "Job Description", "Job Summary", "Job Overview",
        ]

        for section in sections:
            if not section.strip():
                continue

            is_header = False
            section_lower = section.lower().strip()

            for header in section_headers:
                if (
                    section_lower.startswith(header)
                    or section_lower.startswith("• " + header)
                    or section_lower.startswith("- " + header)
                ):
                    current_section = section.strip()
                    is_header = True
                    processed_sections.append(f"\n**{current_section}**\n")
                    break

            if not is_header:
                if section.strip().startswith('•') or section.strip().startswith('-') or section.strip().startswith('*'):
                    lines = section.split('\n')
                    formatted_lines = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                                formatted_lines.append(f"• {line.lstrip('•').lstrip('-').lstrip('*').strip()}")
                            else:
                                formatted_lines.append(line)
                    processed_sections.append('\n'.join(formatted_lines))
                else:
                    processed_sections.append(section.strip())

        return '\n\n'.join(processed_sections)
