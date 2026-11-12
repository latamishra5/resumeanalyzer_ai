import html
import logging
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

logger = logging.getLogger(__name__)


class ResumeBuilder:
    def __init__(self):
        self.templates = {
            "Modern": self.build_modern_template,
            "Professional": self.build_professional_template,
            "Minimal": self.build_minimal_template,
            "Creative": self.build_creative_template,
        }

    def generate_resume(self, data):
        """Generate a resume based on the provided data and template."""
        try:
            template_name = data["template"].lower()
            logger.info("Generating DOCX resume using template=%s", template_name)

            doc = Document()
            if template_name == "modern":
                doc = self.build_modern_template(doc, data)
            elif template_name == "professional":
                doc = self.build_professional_template(doc, data)
            elif template_name == "minimal":
                doc = self.build_minimal_template(doc, data)
            elif template_name == "creative":
                doc = self.build_creative_template(doc, data)
            else:
                logger.warning("Unknown template '%s'; falling back to modern template", template_name)
                doc = self.build_modern_template(doc, data)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            return buffer
        except Exception as exc:
            logger.exception("Error generating resume DOCX: %s", exc)
            raise

    def _format_list_items(self, items):
        """Helper function to handle both string and list inputs"""
        if isinstance(items, str):
            return [item.strip() for item in items.split('\n') if item.strip()]
        elif isinstance(items, list):
            return [item.strip() for item in items if item and item.strip()]
        return []

    def build_modern_template(self, doc, data):
        """Build modern style resume with clean, minimalist design"""
        try:
            # Set up styles
            styles = doc.styles
            
            # Name style - Modern, clean look
            name_style = styles.add_style('Modern Name', WD_STYLE_TYPE.PARAGRAPH) if 'Modern Name' not in styles else styles['Modern Name']
            name_style.font.size = Pt(24)
            name_style.font.bold = True
            name_style.font.color.rgb = RGBColor(41, 128, 185)  # Modern blue
            name_style.font.name = 'Arial'
            name_style.paragraph_format.space_after = Pt(0)
            name_style.paragraph_format.space_before = Pt(6)
            name_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Section style - Clean and modern
            section_style = styles.add_style('Modern Section', WD_STYLE_TYPE.PARAGRAPH) if 'Modern Section' not in styles else styles['Modern Section']
            section_style.font.size = Pt(14)
            section_style.font.bold = True
            section_style.font.color.rgb = RGBColor(41, 128, 185)  # Modern blue
            section_style.font.name = 'Arial'
            section_style.paragraph_format.space_before = Pt(16)
            section_style.paragraph_format.space_after = Pt(4)

            # Section underline style
            section_underline = styles.add_style('Modern Section Underline', WD_STYLE_TYPE.PARAGRAPH) if 'Modern Section Underline' not in styles else styles['Modern Section Underline']
            section_underline.font.size = Pt(8)
            section_underline.font.color.rgb = RGBColor(41, 128, 185)
            section_underline.paragraph_format.space_after = Pt(8)

            # Normal text style
            normal_style = styles.add_style('Modern Normal', WD_STYLE_TYPE.PARAGRAPH) if 'Modern Normal' not in styles else styles['Modern Normal']
            normal_style.font.size = Pt(10)
            normal_style.font.name = 'Arial'
            normal_style.paragraph_format.space_after = Pt(2)
            normal_style.font.color.rgb = RGBColor(44, 62, 80)

            # Contact style
            contact_style = styles.add_style('Modern Contact', WD_STYLE_TYPE.PARAGRAPH) if 'Modern Contact' not in styles else styles['Modern Contact']
            contact_style.font.size = Pt(10)
            contact_style.font.name = 'Arial'
            contact_style.font.color.rgb = RGBColor(41, 128, 185)
            contact_style.paragraph_format.space_after = Pt(2)
            contact_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Add name at the top
            name_paragraph = doc.add_paragraph(data['personal_info']['full_name'].upper())
            name_paragraph.style = name_style

            # Add role/title if available
            if data['personal_info'].get('title'):
                title = doc.add_paragraph(data['personal_info']['title'])
                title.style = contact_style

            # Contact information layout
            contact_info = doc.add_paragraph()
            contact_info.style = contact_style
            
            # Add contact details with separators
            contact_parts = []
            if data['personal_info'].get('email'): contact_parts.append(data['personal_info']['email'])
            if data['personal_info'].get('phone'): contact_parts.append(data['personal_info']['phone'])
            if data['personal_info'].get('location'): contact_parts.append(data['personal_info']['location'])
            if contact_parts:
                contact_info.add_run(' | '.join(contact_parts))

            # Links layout
            if data['personal_info'].get('linkedin') or data['personal_info'].get('portfolio'):
                links = doc.add_paragraph()
                links.style = contact_style
                links_parts = []
                if data['personal_info'].get('linkedin'): links_parts.append(f"LinkedIn: {data['personal_info']['linkedin']}")
                if data['personal_info'].get('portfolio'): links_parts.append(f"Portfolio: {data['personal_info']['portfolio']}")
                links.add_run(' | '.join(links_parts))

            # Professional Summary
            if data.get('summary'):
                doc.add_paragraph('PROFESSIONAL SUMMARY', style=section_style)
                doc.add_paragraph('_' * 40, style=section_underline)
                summary = doc.add_paragraph(data['summary'])
                summary.style = normal_style
                summary.paragraph_format.space_after = Pt(12)
                summary.paragraph_format.left_indent = Inches(0.2)

            # Experience Section
            if data.get('experience'):
                doc.add_paragraph('EXPERIENCE', style=section_style)
                doc.add_paragraph('_' * 40, style=section_underline)
                for exp in data['experience']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)
                    
                    # Company and position
                    p.add_run(f"{exp['position']} at {exp['company']}").bold = True
                    date_run = p.add_run(f"\n{exp['start_date']} - {exp['end_date']}")
                    date_run.font.color.rgb = RGBColor(41, 128, 185)
                    
                    if exp.get('description'):
                        desc = doc.add_paragraph(exp['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.4)
                    
                    if exp.get('responsibilities'):
                        for resp in self._format_list_items(exp['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.6)
                            bullet.add_run('• ' + resp)
                    p.paragraph_format.space_after = Pt(12)

            # Projects Section
            if data.get('projects'):
                doc.add_paragraph('PROJECTS', style=section_style)
                doc.add_paragraph('_' * 40, style=section_underline)
                for proj in data['projects']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)
                    
                    p.add_run(proj['name']).bold = True
                    if proj.get('technologies'):
                        tech_run = p.add_run(f" | {proj['technologies']}")
                        tech_run.font.color.rgb = RGBColor(41, 128, 185)
                    
                    if proj.get('description'):
                        desc = doc.add_paragraph(proj['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.4)
                    
                    if proj.get('responsibilities'):
                        for resp in self._format_list_items(proj['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.6)
                            bullet.add_run('• ' + resp)
                    p.paragraph_format.space_after = Pt(12)

            # Education Section
            if data.get('education'):
                doc.add_paragraph('EDUCATION', style=section_style)
                doc.add_paragraph('_' * 40, style=section_underline)
                for edu in data['education']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)
                    
                    p.add_run(f"{edu['school']}").bold = True
                    p.add_run(f"\n{edu['degree']} in {edu['field']}")
                    date_run = p.add_run(f"\nGraduation: {edu['graduation_date']}")
                    if edu.get('gpa'):
                        p.add_run(f" | GPA: {edu['gpa']}")
                    p.paragraph_format.space_after = Pt(8)

            # Skills Section
            if data.get('skills'):
                doc.add_paragraph('SKILLS', style=section_style)
                doc.add_paragraph('_' * 40, style=section_underline)
                skills = data['skills']
                
                def add_skill_category(category_name, title):
                    if skills.get(category_name):
                        p = doc.add_paragraph()
                        p.style = normal_style
                        p.paragraph_format.left_indent = Inches(0.2)
                        p.add_run(f"{title}: ").bold = True
                        skills_text = ' • '.join(self._format_list_items(skills[category_name]))
                        p.add_run(skills_text)
                        p.paragraph_format.space_after = Pt(6)
                
                add_skill_category('technical', 'Technical Skills')
                add_skill_category('soft', 'Soft Skills')
                add_skill_category('languages', 'Languages')
                add_skill_category('tools', 'Tools & Technologies')

            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.8)
                section.right_margin = Inches(0.8)

            return doc
            
        except Exception as e:
            print(f"Error in build_modern_template: {str(e)}")
            raise

    def build_professional_template(self, doc, data):
        """Build professional style resume with improved spacing and layout"""
        try:
            # Set up styles
            styles = doc.styles
            
            # Header style - Name
            header_style = styles.add_style('Pro Header', WD_STYLE_TYPE.PARAGRAPH) if 'Pro Header' not in styles else styles['Pro Header']
            header_style.font.size = Pt(24)
            header_style.font.bold = True
            header_style.font.color.rgb = RGBColor(0, 0, 0)
            header_style.paragraph_format.space_after = Pt(4)
            header_style.font.name = 'Calibri'

            # Section style
            section_style = styles.add_style('Pro Section', WD_STYLE_TYPE.PARAGRAPH) if 'Pro Section' not in styles else styles['Pro Section']
            section_style.font.size = Pt(14)
            section_style.font.bold = True
            section_style.font.color.rgb = RGBColor(0, 120, 215)
            section_style.paragraph_format.space_before = Pt(12)
            section_style.paragraph_format.space_after = Pt(6)
            section_style.font.name = 'Calibri'

            # Normal text style
            normal_style = styles.add_style('Pro Normal', WD_STYLE_TYPE.PARAGRAPH) if 'Pro Normal' not in styles else styles['Pro Normal']
            normal_style.font.size = Pt(10)
            normal_style.font.name = 'Calibri'
            normal_style.paragraph_format.space_after = Pt(2)

            # Contact style
            contact_style = styles.add_style('Pro Contact', WD_STYLE_TYPE.PARAGRAPH) if 'Pro Contact' not in styles else styles['Pro Contact']
            contact_style.font.size = Pt(10)
            contact_style.font.name = 'Calibri'
            contact_style.paragraph_format.space_after = Pt(6)

            # Add name at the top
            name_paragraph = doc.add_paragraph(data['personal_info']['full_name'])
            name_paragraph.style = header_style
            name_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

            # Add contact information in a single line
            contact_parts = []
            if data['personal_info'].get('email'): contact_parts.append(data['personal_info']['email'])
            if data['personal_info'].get('phone'): contact_parts.append(data['personal_info']['phone'])
            if data['personal_info'].get('location'): contact_parts.append(data['personal_info']['location'])
            
            if contact_parts:
                contact = doc.add_paragraph()
                contact.style = contact_style
                contact.add_run(' | '.join(contact_parts))

            # Add LinkedIn and Portfolio links
            links_parts = []
            if data['personal_info'].get('linkedin'): links_parts.append(f"LinkedIn: {data['personal_info']['linkedin']}")
            if data['personal_info'].get('portfolio'): links_parts.append(f"Portfolio: {data['personal_info']['portfolio']}")
            
            if links_parts:
                links = doc.add_paragraph()
                links.style = contact_style
                links.add_run(' | '.join(links_parts))

            # Professional Summary
            if data.get('summary'):
                doc.add_paragraph('PROFESSIONAL SUMMARY', style=section_style)
                summary = doc.add_paragraph(data['summary'])
                summary.style = normal_style

            # Experience Section
            if data.get('experience'):
                doc.add_paragraph('EXPERIENCE', style=section_style)
                for exp in data['experience']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.add_run(f"{exp['position']} at {exp['company']}").bold = True
                    p.add_run(f" | {exp['start_date']} - {exp['end_date']}")
                    
                    if exp.get('description'):
                        desc = doc.add_paragraph(exp['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.2)
                    
                    if exp.get('responsibilities'):
                        for resp in self._format_list_items(exp['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.3)
                            bullet.add_run('• ' + resp)

            # Projects Section
            if data.get('projects'):
                doc.add_paragraph('PROJECTS', style=section_style)
                for proj in data['projects']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.add_run(proj['name']).bold = True
                    if proj.get('technologies'):
                        p.add_run(f" | {proj['technologies']}")
                    
                    if proj.get('description'):
                        desc = doc.add_paragraph(proj['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.2)
                    
                    if proj.get('responsibilities'):
                        for resp in self._format_list_items(proj['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.3)
                            bullet.add_run('• ' + resp)

            # Education Section
            if data.get('education'):
                doc.add_paragraph('EDUCATION', style=section_style)
                for edu in data['education']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.add_run(f"{edu['school']}").bold = True
                    p.add_run(f"\n{edu['degree']} in {edu['field']}")
                    p.add_run(f" | Graduation: {edu['graduation_date']}")
                    if edu.get('gpa'):
                        p.add_run(f" | GPA: {edu['gpa']}")

            # Skills Section
            if data.get('skills'):
                doc.add_paragraph('SKILLS', style=section_style)
                skills = data['skills']
                
                def add_skill_category(category_name, title):
                    if skills.get(category_name):
                        p = doc.add_paragraph()
                        p.style = normal_style
                        p.add_run(f"{title}: ").bold = True
                        skills_text = ', '.join(self._format_list_items(skills[category_name]))
                        p.add_run(skills_text)
                
                add_skill_category('technical', 'Technical Skills')
                add_skill_category('soft', 'Soft Skills')
                add_skill_category('languages', 'Languages')
                add_skill_category('tools', 'Tools & Technologies')

            # Set margins for better space utilization
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.7)
                section.right_margin = Inches(0.7)

            return doc
            
        except Exception as e:
            print(f"Error in build_professional_template: {str(e)}")
            raise

    def build_minimal_template(self, doc, data):
        """Build minimal style resume"""
        try:
            # Set up styles
            styles = doc.styles
            
            # Header style - Large, bold name
            header_style = None
            if 'Min Header' not in styles:
                header_style = styles.add_style('Min Header', WD_STYLE_TYPE.PARAGRAPH)
                header_style.font.size = Pt(28)
                header_style.font.bold = True
                header_style.font.color.rgb = RGBColor(33, 33, 33)  # Dark gray
                header_style.paragraph_format.space_after = Pt(4)
            else:
                header_style = styles['Min Header']
            
            # Contact style - Small, gray text
            contact_style = None
            if 'Min Contact' not in styles:
                contact_style = styles.add_style('Min Contact', WD_STYLE_TYPE.PARAGRAPH)
                contact_style.font.size = Pt(9)
                contact_style.font.color.rgb = RGBColor(100, 100, 100)  # Light gray
                contact_style.paragraph_format.space_after = Pt(12)
            else:
                contact_style = styles['Min Contact']
            
            # Section style - Medium, all caps
            section_style = None
            if 'Min Section' not in styles:
                section_style = styles.add_style('Min Section', WD_STYLE_TYPE.PARAGRAPH)
                section_style.font.size = Pt(12)
                section_style.font.all_caps = True
                section_style.font.bold = True
                section_style.font.color.rgb = RGBColor(33, 33, 33)
                section_style.paragraph_format.space_before = Pt(16)
                section_style.paragraph_format.space_after = Pt(8)
            else:
                section_style = styles['Min Section']
            
            # Normal text style
            normal_style = None
            if 'Min Normal' not in styles:
                normal_style = styles.add_style('Min Normal', WD_STYLE_TYPE.PARAGRAPH)
                normal_style.font.size = Pt(10)
                normal_style.font.color.rgb = RGBColor(33, 33, 33)
                normal_style.paragraph_format.space_after = Pt(4)
            else:
                normal_style = styles['Min Normal']
            
            # Add header with personal info
            personal = data['personal_info']
            name = doc.add_paragraph(personal['full_name'])
            name.style = header_style
            
            # Contact info in one line
            contact_parts = []
            if personal.get('email'): contact_parts.append(personal['email'])
            if personal.get('phone'): contact_parts.append(personal['phone'])
            if personal.get('location'): contact_parts.append(personal['location'])
            
            if contact_parts:
                contact = doc.add_paragraph()
                contact.style = contact_style
                contact.add_run(' • '.join(contact_parts))
            
            # Links in one line
            links_parts = []
            if personal.get('linkedin'): links_parts.append(f"LinkedIn: {personal['linkedin']}")
            if personal.get('portfolio'): links_parts.append(f"Portfolio: {personal['portfolio']}")
            
            if links_parts:
                links = doc.add_paragraph()
                links.style = contact_style
                links.add_run(' • '.join(links_parts))
            
            # Professional Summary
            if data.get('summary'):
                doc.add_paragraph('SUMMARY', style=section_style)
                summary = doc.add_paragraph(data['summary'])
                summary.style = normal_style
            
            # Experience Section
            if data.get('experience'):
                doc.add_paragraph('EXPERIENCE', style=section_style)
                for exp in data['experience']:
                    p = doc.add_paragraph(style=normal_style)
                    p.add_run(f"{exp['position']} at {exp['company']}").bold = True
                    p.add_run(f"\n{exp['start_date']} - {exp['end_date']}")
                    
                    if exp.get('description'):  # Changed from 'overview' to 'description'
                        overview = doc.add_paragraph(exp['description'])
                        overview.style = normal_style
                    
                    if exp.get('responsibilities'):
                        resp_para = doc.add_paragraph(style=normal_style)
                        resp_para.add_run('Key Responsibilities:').bold = True
                        for resp in self._format_list_items(exp['responsibilities']):
                            bullet = doc.add_paragraph(style=normal_style)
                            bullet.style.paragraph_format.left_indent = Inches(0.25)
                            bullet.add_run('• ' + resp)
                    
                    if exp.get('achievements'):
                        ach_para = doc.add_paragraph(style=normal_style)
                        ach_para.add_run('Key Achievements:').bold = True
                        for ach in self._format_list_items(exp['achievements']):
                            bullet = doc.add_paragraph(style=normal_style)
                            bullet.style.paragraph_format.left_indent = Inches(0.25)
                            bullet.add_run('• ' + ach)
            
            # Projects Section
            if data.get('projects'):
                doc.add_paragraph('PROJECTS', style=section_style)
                for proj in data['projects']:
                    p = doc.add_paragraph(style=normal_style)
                    p.add_run(proj['name']).bold = True
                    if proj.get('technologies'):
                        p.add_run(f"\nTechnologies: {proj['technologies']}")
                    
                    if proj.get('description'):  # Changed from 'overview' to 'description'
                        overview = doc.add_paragraph(proj['description'])
                        overview.style = normal_style
                    
                    if proj.get('responsibilities'):
                        resp_para = doc.add_paragraph(style=normal_style)
                        resp_para.add_run('Key Responsibilities:').bold = True
                        for resp in self._format_list_items(proj['responsibilities']):
                            bullet = doc.add_paragraph(style=normal_style)
                            bullet.style.paragraph_format.left_indent = Inches(0.25)
                            bullet.add_run('• ' + resp)
                    
                    if proj.get('achievements'):
                        ach_para = doc.add_paragraph(style=normal_style)
                        ach_para.add_run('Key Achievements:').bold = True
                        for ach in self._format_list_items(proj['achievements']):
                            bullet = doc.add_paragraph(style=normal_style)
                            bullet.style.paragraph_format.left_indent = Inches(0.25)
                            bullet.add_run('• ' + ach)
                    
                    if proj.get('link'):
                        link = doc.add_paragraph(f"Project Link: {proj['link']}")
                        link.style = normal_style
            
            # Education Section
            if data.get('education'):
                doc.add_paragraph('EDUCATION', style=section_style)
                for edu in data['education']:
                    p = doc.add_paragraph(style=normal_style)
                    p.add_run(f"{edu['school']} - {edu['degree']} in {edu['field']}").bold = True
                    p.add_run(f"\nGraduation: {edu['graduation_date']}")
                    if edu.get('gpa'):
                        p.add_run(f" | GPA: {edu['gpa']}")
                    
                    if edu.get('achievements'):
                        ach_para = doc.add_paragraph(style=normal_style)
                        ach_para.add_run('Achievements & Activities:').bold = True
                        for ach in self._format_list_items(edu['achievements']):
                            bullet = doc.add_paragraph(style=normal_style)
                            bullet.style.paragraph_format.left_indent = Inches(0.25)
                            bullet.add_run('• ' + ach)
            
            # Skills Section
            if data.get('skills'):
                doc.add_paragraph('SKILLS', style=section_style)
                skills = data['skills']
                
                def add_skill_category(category_name, title):
                    if skills.get(category_name):
                        p = doc.add_paragraph(style=normal_style)
                        p.add_run(f"{title}: ").bold = True
                        p.add_run(' • '.join(self._format_list_items(skills[category_name])))
                
                add_skill_category('technical', 'Technical Skills')
                add_skill_category('soft', 'Soft Skills')
                add_skill_category('languages', 'Languages')
                add_skill_category('tools', 'Tools & Technologies')
            
            return doc
            
        except Exception as e:
            print(f"Error in build_minimal_template: {str(e)}")
            raise

    def build_creative_template(self, doc, data):
        """Build creative style resume with vibrant design and emojis"""
        try:
            # Set up styles
            styles = doc.styles
            
            # Name style - Creative and bold
            name_style = styles.add_style('Creative Name', WD_STYLE_TYPE.PARAGRAPH) if 'Creative Name' not in styles else styles['Creative Name']
            name_style.font.size = Pt(24)
            name_style.font.bold = True
            name_style.font.color.rgb = RGBColor(155, 89, 182)  # Purple
            name_style.font.name = 'Arial'
            name_style.paragraph_format.space_after = Pt(4)
            name_style.paragraph_format.space_before = Pt(6)
            name_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Section style - Vibrant
            section_style = styles.add_style('Creative Section', WD_STYLE_TYPE.PARAGRAPH) if 'Creative Section' not in styles else styles['Creative Section']
            section_style.font.size = Pt(14)
            section_style.font.bold = True
            section_style.font.color.rgb = RGBColor(155, 89, 182)  # Purple
            section_style.font.name = 'Arial'
            section_style.paragraph_format.space_before = Pt(16)
            section_style.paragraph_format.space_after = Pt(4)

            # Normal text style - Clean
            normal_style = styles.add_style('Creative Normal', WD_STYLE_TYPE.PARAGRAPH) if 'Creative Normal' not in styles else styles['Creative Normal']
            normal_style.font.size = Pt(10)
            normal_style.font.name = 'Arial'
            normal_style.paragraph_format.space_after = Pt(2)
            normal_style.font.color.rgb = RGBColor(52, 73, 94)  # Dark slate

            # Contact style - Professional
            contact_style = styles.add_style('Creative Contact', WD_STYLE_TYPE.PARAGRAPH) if 'Creative Contact' not in styles else styles['Creative Contact']
            contact_style.font.size = Pt(10)
            contact_style.font.name = 'Arial'
            contact_style.font.color.rgb = RGBColor(155, 89, 182)  # Purple
            contact_style.paragraph_format.space_after = Pt(2)
            contact_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Add name at the top
            name_paragraph = doc.add_paragraph(data['personal_info']['full_name'].upper())
            name_paragraph.style = name_style

            # Add role/title if available
            if data['personal_info'].get('title'):
                title = doc.add_paragraph(data['personal_info']['title'])
                title.style = contact_style

            # Contact information layout
            contact_info = doc.add_paragraph()
            contact_info.style = contact_style

            contact_parts = []
            if data['personal_info'].get('email'):
                contact_parts.append(data['personal_info']['email'])
            if data['personal_info'].get('phone'):
                contact_parts.append(data['personal_info']['phone'])
            if data['personal_info'].get('location'):
                contact_parts.append(data['personal_info']['location'])
            if contact_parts:
                contact_info.add_run(' | '.join(contact_parts))

            # Links with professional formatting
            if data['personal_info'].get('linkedin') or data['personal_info'].get('portfolio'):
                links = doc.add_paragraph()
                links.style = contact_style
                links_parts = []
                if data['personal_info'].get('linkedin'):
                    links_parts.append(f"LinkedIn: {data['personal_info']['linkedin']}")
                if data['personal_info'].get('portfolio'):
                    links_parts.append(f"Portfolio: {data['personal_info']['portfolio']}")
                links.add_run(' | '.join(links_parts))

            # Professional Summary
            if data.get('summary'):
                doc.add_paragraph('PROFESSIONAL SUMMARY', style=section_style)
                summary = doc.add_paragraph(data['summary'])
                summary.style = normal_style
                summary.paragraph_format.space_after = Pt(12)
                summary.paragraph_format.left_indent = Inches(0.2)

            # Experience Section
            if data.get('experience'):
                doc.add_paragraph('EXPERIENCE', style=section_style)
                for exp in data['experience']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)

                    p.add_run(exp['position']).bold = True
                    p.add_run(f"\n{exp['company']}")
                    p.add_run(f"\n{exp['start_date']} - {exp['end_date']}")

                    if exp.get('description'):
                        desc = doc.add_paragraph(exp['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.4)

                    if exp.get('responsibilities'):
                        resp_para = doc.add_paragraph()
                        resp_para.style = normal_style
                        resp_para.paragraph_format.left_indent = Inches(0.4)
                        resp_para.add_run('Key Achievements:').bold = True
                        for resp in self._format_list_items(exp['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.6)
                            bullet.add_run('• ' + resp)
                    p.paragraph_format.space_after = Pt(12)

            # Projects Section
            if data.get('projects'):
                doc.add_paragraph('PROJECTS', style=section_style)
                for proj in data['projects']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)

                    p.add_run(proj['name']).bold = True
                    if proj.get('technologies'):
                        p.add_run(f"\nTechnologies: {proj['technologies']}")

                    if proj.get('description'):
                        desc = doc.add_paragraph(proj['description'])
                        desc.style = normal_style
                        desc.paragraph_format.left_indent = Inches(0.4)

                    if proj.get('responsibilities'):
                        resp_para = doc.add_paragraph()
                        resp_para.style = normal_style
                        resp_para.paragraph_format.left_indent = Inches(0.4)
                        resp_para.add_run('Key Features:').bold = True
                        for resp in self._format_list_items(proj['responsibilities']):
                            bullet = doc.add_paragraph()
                            bullet.style = normal_style
                            bullet.paragraph_format.left_indent = Inches(0.6)
                            bullet.add_run('• ' + resp)
                    p.paragraph_format.space_after = Pt(12)

            # Education Section
            if data.get('education'):
                doc.add_paragraph('EDUCATION', style=section_style)
                for edu in data['education']:
                    p = doc.add_paragraph()
                    p.style = normal_style
                    p.paragraph_format.left_indent = Inches(0.2)

                    p.add_run(edu['school']).bold = True
                    p.add_run(f"\n{edu['degree']} in {edu['field']}")
                    p.add_run(f"\nGraduation: {edu['graduation_date']}")
                    if edu.get('gpa'):
                        p.add_run(f" | GPA: {edu['gpa']}")
                    p.paragraph_format.space_after = Pt(8)

            # Skills Section
            if data.get('skills'):
                doc.add_paragraph('SKILLS', style=section_style)
                skills = data['skills']

                def add_skill_category(category_name, title):
                    if skills.get(category_name):
                        p = doc.add_paragraph()
                        p.style = normal_style
                        p.paragraph_format.left_indent = Inches(0.2)
                        p.add_run(f"{title}: ").bold = True
                        skills_text = ' • '.join(self._format_list_items(skills[category_name]))
                        p.add_run(skills_text)
                        p.paragraph_format.space_after = Pt(6)

                add_skill_category('technical', 'Technical Skills')
                add_skill_category('soft', 'Soft Skills')
                add_skill_category('languages', 'Languages')
                add_skill_category('tools', 'Tools & Technologies')

            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.8)
                section.right_margin = Inches(0.8)

            return doc
            
        except Exception as e:
            print(f"Error in build_creative_template: {str(e)}")
            raise

    def render_resume_html_preview(self, data: dict) -> str:
        """Render a clean, XSS-safe HTML resume preview card matching the selected template."""
        personal = data.get("personal_info", {}) or {}
        template_name = str(data.get("template") or "Modern").strip()
        accent_map = {
            "Modern": "#2563eb",
            "Professional": "#0f766e",
            "Minimal": "#334155",
            "Creative": "#7c3aed",
        }
        accent = accent_map.get(template_name, "#2563eb")

        name = html.escape(str(personal.get("full_name") or "Your Name"), quote=True)
        contact_parts = [
            html.escape(str(v), quote=True)
            for v in (
                personal.get("email"),
                personal.get("phone"),
                personal.get("location"),
                personal.get("linkedin"),
                personal.get("portfolio"),
            )
            if str(v or "").strip()
        ]
        contact_line = " &middot; ".join(contact_parts) if contact_parts else "email@example.com &middot; Location"

        sections_html = []
        summary = str(data.get("summary") or "").strip()
        if summary:
            sections_html.append(
                f"<h4 style='color:{accent};border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:14px 0 6px;'>SUMMARY</h4>"
                f"<p style='margin:0;color:#1e293b;line-height:1.45;'>{html.escape(summary, quote=True)}</p>"
            )

        experiences = data.get("experience") or data.get("experiences") or []
        if experiences:
            exp_blocks = []
            for exp in experiences:
                role = html.escape(str(exp.get("position") or exp.get("title") or "Role"), quote=True)
                company = html.escape(str(exp.get("company") or ""), quote=True)
                dates = " - ".join(
                    html.escape(str(d), quote=True)
                    for d in (exp.get("start_date"), exp.get("end_date"))
                    if str(d or "").strip()
                )
                desc = str(exp.get("description") or "").strip()
                bullets = list(exp.get("responsibilities") or []) + list(exp.get("achievements") or [])
                bullet_html = "".join(
                    f"<li>{html.escape(str(b), quote=True)}</li>" for b in bullets if str(b or "").strip()
                )
                exp_blocks.append(
                    f"<div style='margin-bottom:10px;'>"
                    f"<div style='display:flex;justify-content:space-between;'><strong>{role}</strong>"
                    f"<span style='color:#475569;font-size:0.85rem;'>{dates}</span></div>"
                    f"<div style='color:#334155;font-size:0.9rem;'>{company}</div>"
                    f"{f'<p style=\"margin:4px 0;color:#1e293b;\">{html.escape(desc, quote=True)}</p>' if desc else ''}"
                    f"{f'<ul style=\"margin:4px 0 0 18px;color:#1e293b;\">{bullet_html}</ul>' if bullet_html else ''}"
                    f"</div>"
                )
            sections_html.append(
                f"<h4 style='color:{accent};border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:14px 0 6px;'>EXPERIENCE</h4>"
                + "".join(exp_blocks)
            )

        projects = data.get("projects") or []
        if projects:
            proj_blocks = []
            for proj in projects:
                pname = html.escape(str(proj.get("name") or "Project"), quote=True)
                tech = html.escape(str(proj.get("technologies") or ""), quote=True)
                pdesc = str(proj.get("description") or "").strip()
                proj_blocks.append(
                    f"<div style='margin-bottom:8px;'>"
                    f"<strong>{pname}</strong>"
                    f"{f' <span style=\"color:#475569;font-size:0.85rem;\">({tech})</span>' if tech else ''}"
                    f"{f'<p style=\"margin:2px 0;color:#1e293b;\">{html.escape(pdesc, quote=True)}</p>' if pdesc else ''}"
                    f"</div>"
                )
            sections_html.append(
                f"<h4 style='color:{accent};border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:14px 0 6px;'>PROJECTS</h4>"
                + "".join(proj_blocks)
            )

        education = data.get("education") or []
        if education:
            edu_blocks = []
            for edu in education:
                school = html.escape(str(edu.get("school") or "Institution"), quote=True)
                degree = html.escape(str(edu.get("degree") or ""), quote=True)
                field = html.escape(str(edu.get("field") or ""), quote=True)
                grad = html.escape(str(edu.get("graduation_date") or ""), quote=True)
                gpa = html.escape(str(edu.get("gpa") or ""), quote=True)
                detail = " ".join(p for p in (degree, f"in {field}" if field else "") if p).strip()
                meta = " &middot; ".join(p for p in (grad, f"GPA: {gpa}" if gpa else "") if p)
                edu_blocks.append(
                    f"<div style='margin-bottom:6px;'><strong>{school}</strong>"
                    f"{f' &mdash; {detail}' if detail else ''}"
                    f"{f' <span style=\"color:#475569;font-size:0.85rem;\">({meta})</span>' if meta else ''}</div>"
                )
            sections_html.append(
                f"<h4 style='color:{accent};border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:14px 0 6px;'>EDUCATION</h4>"
                + "".join(edu_blocks)
            )

        skills = data.get("skills") or {}
        if isinstance(skills, dict):
            skill_lines = []
            for key, title in (
                ("technical", "Technical"),
                ("tools", "Tools"),
                ("languages", "Languages"),
                ("soft", "Soft Skills"),
            ):
                items = [html.escape(str(s), quote=True) for s in (skills.get(key) or []) if str(s or "").strip()]
                if items:
                    skill_lines.append(f"<div><strong>{title}:</strong> {', '.join(items)}</div>")
            if skill_lines:
                sections_html.append(
                    f"<h4 style='color:{accent};border-bottom:1px solid #cbd5e1;padding-bottom:4px;margin:14px 0 6px;'>SKILLS</h4>"
                    + "".join(skill_lines)
                )

        body = "".join(sections_html) or "<p style='color:#64748b;'>Fill out sections above to see a live document preview.</p>"
        return (
            f"<div style='background:#ffffff;color:#0f172a;padding:24px 28px;border-radius:10px;"
            f"border-top:6px solid {accent};box-shadow:0 4px 16px rgba(0,0,0,0.2);font-family:Segoe UI,Arial,sans-serif;'>"
            f"<div style='text-align:center;margin-bottom:10px;'>"
            f"<h2 style='margin:0;color:{accent};'>{name}</h2>"
            f"<div style='color:#475569;font-size:0.88rem;margin-top:4px;'>{contact_line}</div>"
            f"</div>{body}</div>"
        )

    def generate_resume_pdf(self, data: dict):
        """Generate an ATS-friendly PDF version of the built resume via ReportLab."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.65 * inch,
                rightMargin=0.65 * inch,
                topMargin=0.6 * inch,
                bottomMargin=0.6 * inch,
            )
            styles = getSampleStyleSheet()
            accent_hex = {
                "Modern": "#1d4ed8",
                "Professional": "#0f766e",
                "Minimal": "#1e293b",
                "Creative": "#6d28d9",
            }.get(str(data.get("template") or "Modern").strip(), "#1d4ed8")
            accent = colors.HexColor(accent_hex)

            name_style = ParagraphStyle(
                "ResumeName",
                parent=styles["Heading1"],
                fontSize=19,
                leading=22,
                textColor=accent,
                alignment=1,
                spaceAfter=4,
            )
            contact_style = ParagraphStyle(
                "ResumeContact",
                parent=styles["Normal"],
                fontSize=9.5,
                leading=12,
                textColor=colors.HexColor("#475569"),
                alignment=1,
                spaceAfter=10,
            )
            sec_style = ParagraphStyle(
                "ResumeSec",
                parent=styles["Heading2"],
                fontSize=11,
                leading=14,
                textColor=accent,
                spaceBefore=8,
                spaceAfter=4,
            )
            body_style = ParagraphStyle(
                "ResumeBody",
                parent=styles["Normal"],
                fontSize=10,
                leading=13.5,
                textColor=colors.HexColor("#0f172a"),
                spaceAfter=3,
            )
            bullet_style = ParagraphStyle(
                "ResumeBullet",
                parent=body_style,
                leftIndent=14,
                spaceAfter=2,
            )

            personal = data.get("personal_info", {}) or {}
            story = [
                Paragraph(xml_escape(str(personal.get("full_name") or "Resume")), name_style),
            ]
            contact_vals = [
                xml_escape(str(v).strip())
                for v in (
                    personal.get("email"),
                    personal.get("phone"),
                    personal.get("location"),
                    personal.get("linkedin"),
                    personal.get("portfolio"),
                )
                if str(v or "").strip()
            ]
            if contact_vals:
                story.append(Paragraph(" | ".join(contact_vals), contact_style))

            def add_heading(title):
                story.append(Paragraph(title, sec_style))
                story.append(HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#cbd5e1"), spaceAfter=4))

            if str(data.get("summary") or "").strip():
                add_heading("PROFESSIONAL SUMMARY")
                story.append(Paragraph(xml_escape(str(data["summary"]).strip()), body_style))

            experiences = data.get("experience") or data.get("experiences") or []
            if experiences:
                add_heading("EXPERIENCE")
                for exp in experiences:
                    pos = xml_escape(str(exp.get("position") or exp.get("title") or "Role"))
                    comp = xml_escape(str(exp.get("company") or ""))
                    dates = " - ".join(
                        xml_escape(str(d).strip())
                        for d in (exp.get("start_date"), exp.get("end_date"))
                        if str(d or "").strip()
                    )
                    header = f"<b>{pos}</b>" + (f" — {comp}" if comp else "") + (f" ({dates})" if dates else "")
                    story.append(Paragraph(header, body_style))
                    if str(exp.get("description") or "").strip():
                        story.append(Paragraph(xml_escape(str(exp["description"]).strip()), body_style))
                    for item in list(exp.get("responsibilities") or []) + list(exp.get("achievements") or []):
                        if str(item or "").strip():
                            story.append(Paragraph(f"- {xml_escape(str(item).strip())}", bullet_style))
                    story.append(Spacer(1, 4))

            projects = data.get("projects") or []
            if projects:
                add_heading("PROJECTS")
                for proj in projects:
                    pname = xml_escape(str(proj.get("name") or "Project"))
                    tech = xml_escape(str(proj.get("technologies") or ""))
                    story.append(Paragraph(f"<b>{pname}</b>" + (f" ({tech})" if tech else ""), body_style))
                    if str(proj.get("description") or "").strip():
                        story.append(Paragraph(xml_escape(str(proj["description"]).strip()), body_style))
                    for item in list(proj.get("responsibilities") or []) + list(proj.get("achievements") or []):
                        if str(item or "").strip():
                            story.append(Paragraph(f"- {xml_escape(str(item).strip())}", bullet_style))

            education = data.get("education") or []
            if education:
                add_heading("EDUCATION")
                for edu in education:
                    school = xml_escape(str(edu.get("school") or ""))
                    deg = xml_escape(str(edu.get("degree") or ""))
                    fld = xml_escape(str(edu.get("field") or ""))
                    grad = xml_escape(str(edu.get("graduation_date") or ""))
                    gpa = xml_escape(str(edu.get("gpa") or ""))
                    line = f"<b>{school}</b>"
                    if deg or fld:
                        line += f" — {deg} {fld}".strip()
                    if grad:
                        line += f" | {grad}"
                    if gpa:
                        line += f" | GPA: {gpa}"
                    story.append(Paragraph(line, body_style))

            skills = data.get("skills") or {}
            if isinstance(skills, dict) and any(skills.values()):
                add_heading("SKILLS")
                for key, title in (
                    ("technical", "Technical Skills"),
                    ("tools", "Tools & Technologies"),
                    ("languages", "Languages"),
                    ("soft", "Soft Skills"),
                ):
                    items = [xml_escape(str(s).strip()) for s in (skills.get(key) or []) if str(s or "").strip()]
                    if items:
                        story.append(Paragraph(f"<b>{title}:</b> {', '.join(items)}", body_style))

            doc.build(story)
            buffer.seek(0)
            return buffer
        except Exception as exc:
            logger.exception("Error generating PDF resume: %s", exc)
            return None

    def generate_preview(self, template_name, data):
        """Generate a live HTML preview payload of the resume."""
        merged = dict(data or {})
        merged.setdefault("template", template_name)
        return {
            "html": self.render_resume_html_preview(merged),
            "css": "",
        }