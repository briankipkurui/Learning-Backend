from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, KeepTogether
from reportlab.lib import colors
from io import BytesIO

# Helper function to create bullet lists
def create_bullet_list(items, style):
    """Create a bulleted list from an array of items"""
    if not items:
        return None
    
    # Create custom style with no extra indentation to prevent overlap
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=style,
        leftIndent=0,
        firstLineIndent=0
    )
    
    list_items = []
    for item in items:
        list_items.append(ListItem(Paragraph(item, bullet_style), leftIndent=0))
    
    return ListFlowable(
        list_items,
        bulletType='bullet',
        bulletFontSize=10,
        bulletColor=colors.HexColor('#3498DB'),
        leftIndent=20,
        bulletOffsetY=-1,
        start=None
    )

def generate_resume_pdf(resume_data: dict, user_id: str) -> bytes:
    """
    Generates a PDF file from the provided resume data structure.

    Args:
        resume_data: Dictionary containing resume sections from optimized_resume JSON
        user_id: User identifier for tracking/naming
        
    Returns:
        bytes: PDF file content as bytes
    """
    
    # Use BytesIO to generate PDF in memory instead of file
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles for better formatting
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        keepWithNext=True
    )
    
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#BDC3C7'),
        borderPadding=4,
        borderRadius=2,
        keepWithNext=True
    )
    
    job_title_style = ParagraphStyle(
        'JobTitle',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=2,
        fontName='Helvetica-Bold',
        keepWithNext=True
    )
    
    company_style = ParagraphStyle(
        'Company',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7F8C8D'),
        spaceAfter=6,
        fontName='Helvetica-Oblique',
        keepWithNext=True
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50'),
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    # Professional Summary
    if resume_data.get("professional_summary"):
        story.append(Paragraph("Professional Summary", section_header_style))
        story.append(Paragraph(resume_data["professional_summary"], normal_style))
        story.append(Spacer(1, 12))
    
    # Core Competencies
    if resume_data.get("core_competencies"):
        competencies_elements = []
        competencies_elements.append(Paragraph("Core Competencies", section_header_style))
        
        # Format competencies as bulleted list
        competencies = resume_data["core_competencies"]
        if isinstance(competencies, list):
            bullet_list = create_bullet_list(competencies, normal_style)
            if bullet_list:
                competencies_elements.append(bullet_list)
        else:
            competencies_elements.append(Paragraph(str(competencies), normal_style))
        
        competencies_elements.append(Spacer(1, 12))
        
        # Keep competencies section together
        story.append(KeepTogether(competencies_elements))
    
    # Professional Experience
    if resume_data.get("experience"):
        story.append(Paragraph("Professional Experience", section_header_style))
        
        for job in resume_data["experience"]:
            # Wrap each job entry in KeepTogether to prevent page breaks
            job_elements = []
            
            job_title = job.get("title", "")
            company = job.get("company", "")
            duration = job.get("duration", "")
            
            job_elements.append(Paragraph(job_title, job_title_style))
            job_elements.append(Paragraph(f"{company} | {duration}", company_style))
            
            # Achievements as bullet points
            achievements = job.get("achievements", [])
            if achievements:
                bullet_list = create_bullet_list(achievements, normal_style)
                if bullet_list:
                    job_elements.append(bullet_list)
            
            job_elements.append(Spacer(1, 8))
            
            # Keep all job elements together on same page
            try:
                story.append(KeepTogether(job_elements))
            except:
                # If job entry is too large for one page, add without KeepTogether
                story.extend(job_elements)
        
        story.append(Spacer(1, 12))
    
    # Education
    if resume_data.get("education"):
        story.append(Paragraph("Education", section_header_style))
        
        for edu in resume_data["education"]:
            # Wrap each education entry in KeepTogether
            edu_elements = []
            
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            
            edu_elements.append(Paragraph(degree, job_title_style))
            edu_elements.append(Paragraph(f"{institution} | {year}", company_style))
            edu_elements.append(Spacer(1, 6))
            
            # Keep education entry together
            story.append(KeepTogether(edu_elements))
        
        story.append(Spacer(1, 12))
    
    # Additional Sections
    if resume_data.get("additional_sections"):
        additional = resume_data["additional_sections"]
        
        # Certifications
        if additional.get("certifications"):
            cert_elements = []
            cert_elements.append(Paragraph("Certifications", section_header_style))
            bullet_list = create_bullet_list(additional["certifications"], normal_style)
            if bullet_list:
                cert_elements.append(bullet_list)
            cert_elements.append(Spacer(1, 8))
            story.append(KeepTogether(cert_elements))
        
        # Technical Skills
        if additional.get("technical_skills"):
            skills_elements = []
            skills_elements.append(Paragraph("Technical Skills", section_header_style))
            skills_text = " • ".join(additional["technical_skills"])
            skills_elements.append(Paragraph(skills_text, normal_style))
            skills_elements.append(Spacer(1, 8))
            story.append(KeepTogether(skills_elements))
        
        # Languages
        if additional.get("languages"):
            lang_elements = []
            lang_elements.append(Paragraph("Languages", section_header_style))
            languages_text = " • ".join(additional["languages"])
            lang_elements.append(Paragraph(languages_text, normal_style))
            lang_elements.append(Spacer(1, 8))
            story.append(KeepTogether(lang_elements))
    
    # Build the PDF
    doc.build(story)
    
    # Get PDF bytes from buffer
    pdf_bytes = buffer.getvalue()

    buffer.close()
    
    return pdf_bytes