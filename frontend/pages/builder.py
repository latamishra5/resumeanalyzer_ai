"""Resume builder page view."""

import logging
import streamlit as st

from backend.auth.auth_service import AuthService
from backend.database.connection import save_resume_data

logger = logging.getLogger(__name__)


def _apply_prefill_to_form_data(personal: dict, summary: str = "", skills_list: list | None = None):
    """Apply prefill contact, summary, and skills cleanly into builder session state."""
    pinfo = st.session_state.form_data["personal_info"]
    for src_key, dst_key in (
        ("full_name", "full_name"),
        ("name", "full_name"),
        ("email", "email"),
        ("phone", "phone"),
        ("location", "location"),
        ("linkedin", "linkedin"),
        ("portfolio", "portfolio"),
    ):
        val = str(personal.get(src_key) or "").strip()
        if val and (dst_key != "full_name" or not pinfo.get("full_name")):
            pinfo[dst_key] = val
    if summary and not st.session_state.form_data.get("summary"):
        st.session_state.form_data["summary"] = summary.strip()
    if skills_list:
        existing_tech = st.session_state.form_data["skills_categories"].get("technical", [])
        merged = list(dict.fromkeys([*existing_tech, *(str(s).strip() for s in skills_list if str(s).strip())]))
        st.session_state.form_data["skills_categories"]["technical"] = merged
    if pinfo.get("email"):
        st.session_state["email_input"] = pinfo["email"]


def render_builder(builder):
    st.title("Resume Builder")
    st.write("Create your professional resume")

    # Template selection
    template_options = ["Modern", "Professional", "Minimal", "Creative"]
    selected_template = st.selectbox("Select Resume Template", template_options)
    st.success(f"Currently using: {selected_template} Template", icon=":material/palette:")

    is_authed = bool(
        st.session_state.get("authenticated") and isinstance(st.session_state.get("user_id"), int)
    )
    has_parsed = bool(st.session_state.get("last_parsed_resume"))
    if is_authed or has_parsed:
        pre_col1, pre_col2 = st.columns(2)
        with pre_col1:
            if is_authed and st.button("Pre-fill from My Profile", icon=":material/person:", key="prefill_profile_btn"):
                profile = AuthService().get_user_profile(st.session_state["user_id"])
                if profile:
                    _apply_prefill_to_form_data(profile)
                    st.success("Loaded contact fields from your account profile.")
                    st.rerun()
        with pre_col2:
            if has_parsed and st.button("Pre-fill from Analyzed Resume", icon=":material/auto_fix_high:", key="prefill_parsed_btn"):
                parsed = st.session_state["last_parsed_resume"]
                _apply_prefill_to_form_data(
                    parsed.get("personal_info", {}),
                    summary=parsed.get("summary", ""),
                    skills_list=st.session_state.get("last_resume_skills") or parsed.get("skills", []),
                )
                st.success("Loaded details from your last analyzed resume.")
                st.rerun()

    # Personal Information
    st.subheader("Personal Information")

    col1, col2 = st.columns(2)
    with col1:
        existing_name = st.session_state.form_data['personal_info']['full_name']
        existing_email = st.session_state.form_data['personal_info']['email']
        existing_phone = st.session_state.form_data['personal_info']['phone']

        full_name = st.text_input("Full Name", value=existing_name)
        email = st.text_input("Email", value=existing_email, key="email_input")
        phone = st.text_input("Phone", value=existing_phone)

        if 'email_input' in st.session_state:
            st.session_state.form_data['personal_info']['email'] = st.session_state.email_input

    with col2:
        existing_location = st.session_state.form_data['personal_info']['location']
        existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
        existing_portfolio = st.session_state.form_data['personal_info']['portfolio']

        location = st.text_input("Location", value=existing_location)
        linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
        portfolio = st.text_input("Portfolio Website", value=existing_portfolio)

    st.session_state.form_data['personal_info'] = {
        'full_name': full_name,
        'email': email,
        'phone': phone,
        'location': location,
        'linkedin': linkedin,
        'portfolio': portfolio,
    }

    # Professional Summary
    st.subheader("Professional Summary")
    summary = st.text_area(
        "Professional Summary",
        value=st.session_state.form_data.get('summary', ''),
        height=150,
        help="Write a brief summary highlighting your key skills and experience",
    )

    # Experience Section
    st.subheader("Work Experience")
    if 'experiences' not in st.session_state.form_data:
        st.session_state.form_data['experiences'] = []

    if st.button("Add Experience"):
        st.session_state.form_data['experiences'].append({
            'company': '',
            'position': '',
            'start_date': '',
            'end_date': '',
            'description': '',
            'responsibilities': [],
            'achievements': [],
        })

    for idx, exp in enumerate(st.session_state.form_data['experiences']):
        with st.expander(f"Experience {idx + 1}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                exp['company'] = st.text_input("Company Name", key=f"company_{idx}", value=exp.get('company', ''))
                exp['position'] = st.text_input("Position", key=f"position_{idx}", value=exp.get('position', ''))
            with col2:
                exp['start_date'] = st.text_input("Start Date", key=f"start_date_{idx}", value=exp.get('start_date', ''))
                exp['end_date'] = st.text_input("End Date", key=f"end_date_{idx}", value=exp.get('end_date', ''))

            exp['description'] = st.text_area(
                "Role Overview",
                key=f"desc_{idx}",
                value=exp.get('description', ''),
                help="Brief overview of your role and impact",
            )

            st.markdown("##### Key Responsibilities")
            resp_text = st.text_area(
                "Enter responsibilities (one per line)",
                key=f"resp_{idx}",
                value='\n'.join(exp.get('responsibilities', [])),
                height=100,
                help="List your main responsibilities, one per line",
            )
            exp['responsibilities'] = [r.strip() for r in resp_text.split('\n') if r.strip()]

            st.markdown("##### Key Achievements")
            achv_text = st.text_area(
                "Enter achievements (one per line)",
                key=f"achv_{idx}",
                value='\n'.join(exp.get('achievements', [])),
                height=100,
                help="List your notable achievements, one per line",
            )
            exp['achievements'] = [a.strip() for a in achv_text.split('\n') if a.strip()]

            if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                st.session_state.form_data['experiences'].pop(idx)
                st.rerun()

    # Projects Section
    st.subheader("Projects")
    if 'projects' not in st.session_state.form_data:
        st.session_state.form_data['projects'] = []

    if st.button("Add Project"):
        st.session_state.form_data['projects'].append({
            'name': '',
            'technologies': '',
            'description': '',
            'responsibilities': [],
            'achievements': [],
            'link': '',
        })

    for idx, proj in enumerate(st.session_state.form_data['projects']):
        with st.expander(f"Project {idx + 1}", expanded=True):
            proj['name'] = st.text_input("Project Name", key=f"proj_name_{idx}", value=proj.get('name', ''))
            proj['technologies'] = st.text_input(
                "Technologies Used",
                key=f"proj_tech_{idx}",
                value=proj.get('technologies', ''),
                help="List the main technologies, frameworks, and tools used",
            )

            proj['description'] = st.text_area(
                "Project Overview",
                key=f"proj_desc_{idx}",
                value=proj.get('description', ''),
                help="Brief overview of the project and its goals",
            )

            st.markdown("##### Key Responsibilities")
            proj_resp_text = st.text_area(
                "Enter responsibilities (one per line)",
                key=f"proj_resp_{idx}",
                value='\n'.join(proj.get('responsibilities', [])),
                height=100,
                help="List your main responsibilities in the project",
            )
            proj['responsibilities'] = [r.strip() for r in proj_resp_text.split('\n') if r.strip()]

            st.markdown("##### Key Achievements")
            proj_achv_text = st.text_area(
                "Enter achievements (one per line)",
                key=f"proj_achv_{idx}",
                value='\n'.join(proj.get('achievements', [])),
                height=100,
                help="List the project's key achievements and your contributions",
            )
            proj['achievements'] = [a.strip() for a in proj_achv_text.split('\n') if a.strip()]

            proj['link'] = st.text_input(
                "Project Link (optional)",
                key=f"proj_link_{idx}",
                value=proj.get('link', ''),
                help="Link to the project repository, demo, or documentation",
            )

            if st.button("Remove Project", key=f"remove_proj_{idx}"):
                st.session_state.form_data['projects'].pop(idx)
                st.rerun()

    # Education Section
    st.subheader("Education")
    if 'education' not in st.session_state.form_data:
        st.session_state.form_data['education'] = []

    if st.button("Add Education"):
        st.session_state.form_data['education'].append({
            'school': '',
            'degree': '',
            'field': '',
            'graduation_date': '',
            'gpa': '',
            'achievements': [],
        })

    for idx, edu in enumerate(st.session_state.form_data['education']):
        with st.expander(f"Education {idx + 1}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                edu['school'] = st.text_input("School/University", key=f"school_{idx}", value=edu.get('school', ''))
                edu['degree'] = st.text_input("Degree", key=f"degree_{idx}", value=edu.get('degree', ''))
            with col2:
                edu['field'] = st.text_input("Field of Study", key=f"field_{idx}", value=edu.get('field', ''))
                edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}", value=edu.get('graduation_date', ''))

            edu['gpa'] = st.text_input("GPA (optional)", key=f"gpa_{idx}", value=edu.get('gpa', ''))

            st.markdown("##### Achievements & Activities")
            edu_achv_text = st.text_area(
                "Enter achievements (one per line)",
                key=f"edu_achv_{idx}",
                value='\n'.join(edu.get('achievements', [])),
                height=100,
                help="List academic achievements, relevant coursework, or activities",
            )
            edu['achievements'] = [a.strip() for a in edu_achv_text.split('\n') if a.strip()]

            if st.button("Remove Education", key=f"remove_edu_{idx}"):
                st.session_state.form_data['education'].pop(idx)
                st.rerun()

    # Skills Section
    st.subheader("Skills")
    if 'skills_categories' not in st.session_state.form_data:
        st.session_state.form_data['skills_categories'] = {
            'technical': [],
            'soft': [],
            'languages': [],
            'tools': [],
        }

    col1, col2 = st.columns(2)
    with col1:
        tech_skills = st.text_area(
            "Technical Skills (one per line)",
            value='\n'.join(st.session_state.form_data['skills_categories']['technical']),
            height=150,
            help="Programming languages, frameworks, databases, etc.",
        )
        st.session_state.form_data['skills_categories']['technical'] = [
            s.strip() for s in tech_skills.split('\n') if s.strip()
        ]

        soft_skills = st.text_area(
            "Soft Skills (one per line)",
            value='\n'.join(st.session_state.form_data['skills_categories']['soft']),
            height=150,
            help="Leadership, communication, problem-solving, etc.",
        )
        st.session_state.form_data['skills_categories']['soft'] = [
            s.strip() for s in soft_skills.split('\n') if s.strip()
        ]

    with col2:
        languages = st.text_area(
            "Languages (one per line)",
            value='\n'.join(st.session_state.form_data['skills_categories']['languages']),
            height=150,
            help="Programming or human languages with proficiency level",
        )
        st.session_state.form_data['skills_categories']['languages'] = [
            l.strip() for l in languages.split('\n') if l.strip()
        ]

        tools = st.text_area(
            "Tools & Technologies (one per line)",
            value='\n'.join(st.session_state.form_data['skills_categories']['tools']),
            height=150,
            help="Development tools, software, platforms, etc.",
        )
        st.session_state.form_data['skills_categories']['tools'] = [
            t.strip() for t in tools.split('\n') if t.strip()
        ]

    st.session_state.form_data.update({'summary': summary})

    live_payload = {
        "personal_info": st.session_state.form_data['personal_info'],
        "summary": st.session_state.form_data.get('summary', '').strip(),
        "experience": st.session_state.form_data.get('experiences', []),
        "education": st.session_state.form_data.get('education', []),
        "projects": st.session_state.form_data.get('projects', []),
        "skills": st.session_state.form_data.get('skills_categories', {}),
        "template": selected_template,
    }

    with st.expander(":material/visibility: Live Resume Preview", expanded=False):
        st.markdown(builder.render_resume_html_preview(live_payload), unsafe_allow_html=True)

    # Generate Resume button
    if st.button("Generate Resume", icon=":material/description:", type="primary"):
        logger.info("Validating resume builder form data")

        current_name = st.session_state.form_data['personal_info']['full_name'].strip()
        current_email = st.session_state.email_input if 'email_input' in st.session_state else ''

        if not current_name:
            st.error("Please enter your full name.", icon=":material/warning:")
            return

        if not current_email:
            st.error("Please enter your email address.", icon=":material/warning:")
            return

        st.session_state.form_data['personal_info']['email'] = current_email

        try:
            resume_data = {
                "personal_info": st.session_state.form_data['personal_info'],
                "summary": st.session_state.form_data.get('summary', '').strip(),
                "experience": st.session_state.form_data.get('experiences', []),
                "education": st.session_state.form_data.get('education', []),
                "projects": st.session_state.form_data.get('projects', []),
                "skills": st.session_state.form_data.get('skills_categories', {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': [],
                }),
                "template": selected_template,
            }

            try:
                resume_buffer = builder.generate_resume(resume_data)
                pdf_buffer = builder.generate_resume_pdf(resume_data)
                if resume_buffer:
                    active_uid = st.session_state.get("user_id") if st.session_state.get("authenticated") else None
                    try:
                        save_resume_data(resume_data, user_id=active_uid)
                        st.success("Resume generated successfully.")
                    except Exception as db_error:
                        logger.warning("Failed to save generated resume to database: %s", db_error)
                        st.warning("Resume generated, though it could not be saved to history.")

                    dl_col1, dl_col2 = st.columns(2)
                    safe_base = current_name.replace(' ', '_')
                    with dl_col1:
                        st.download_button(
                            label="Download Resume (.docx)",
                            icon=":material/download:",
                            data=resume_buffer,
                            file_name=f"{safe_base}_resume.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            width="stretch",
                        )
                    with dl_col2:
                        if pdf_buffer:
                            st.download_button(
                                label="Download Resume (.pdf)",
                                icon=":material/picture_as_pdf:",
                                data=pdf_buffer,
                                file_name=f"{safe_base}_resume.pdf",
                                mime="application/pdf",
                                width="stretch",
                            )
                else:
                    st.error("Failed to generate resume. Please try again.")
                    logger.error("Resume builder returned empty buffer")
            except Exception as gen_error:
                logger.exception("Error during resume generation: %s", gen_error)
                st.error(f"Error generating resume: {str(gen_error)}")

        except Exception as e:
            logger.exception("Error preparing resume data: %s", e)
            st.error(f"Error preparing resume data: {str(e)}")
