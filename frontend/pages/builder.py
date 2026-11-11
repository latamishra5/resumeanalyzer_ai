"""Resume builder page view."""

import traceback
import streamlit as st

from backend.database.connection import save_resume_data


def render_builder(builder):
    st.title("Resume Builder 📝")
    st.write("Create your professional resume")

    # Template selection
    template_options = ["Modern", "Professional", "Minimal", "Creative"]
    selected_template = st.selectbox("Select Resume Template", template_options)
    st.success(f"🎨 Currently using: {selected_template} Template")

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

    # Generate Resume button
    if st.button("Generate Resume 📄", type="primary"):
        print("Validating form data...")
        print(f"Session state form data: {st.session_state.form_data}")
        print(f"Email input value: {st.session_state.get('email_input', '')}")

        current_name = st.session_state.form_data['personal_info']['full_name'].strip()
        current_email = st.session_state.email_input if 'email_input' in st.session_state else ''

        print(f"Current name: {current_name}")
        print(f"Current email: {current_email}")

        if not current_name:
            st.error("⚠️ Please enter your full name.")
            return

        if not current_email:
            st.error("⚠️ Please enter your email address.")
            return

        st.session_state.form_data['personal_info']['email'] = current_email

        try:
            print("Preparing resume data...")
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

            print(f"Resume data prepared: {resume_data}")

            try:
                resume_buffer = builder.generate_resume(resume_data)
                if resume_buffer:
                    try:
                        save_resume_data(resume_data)
                        st.success("✅ Resume generated successfully!")
                        st.snow()
                        st.download_button(
                            label="Download Resume 📥",
                            data=resume_buffer,
                            file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            on_click=lambda: st.balloons(),
                        )
                    except Exception as db_error:
                        print(f"Warning: Failed to save to database: {str(db_error)}")
                        st.warning("⚠️ Resume generated but couldn't be saved to database")
                        st.balloons()
                        st.download_button(
                            label="Download Resume 📥",
                            data=resume_buffer,
                            file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            on_click=lambda: st.balloons(),
                        )
                else:
                    st.error("❌ Failed to generate resume. Please try again.")
                    print("Resume buffer was None")
            except Exception as gen_error:
                print(f"Error during resume generation: {str(gen_error)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error generating resume: {str(gen_error)}")

        except Exception as e:
            print(f"Error preparing resume data: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            st.error(f"❌ Error preparing resume data: {str(e)}")

    st.toast("Check out these repositories: [30-Days-Of-Rust](https://github.com/latamishra5/30-Days-Of-Rust)", icon="ℹ️")
