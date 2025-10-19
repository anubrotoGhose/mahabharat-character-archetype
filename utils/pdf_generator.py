# utils/pdf_generator.py
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import io
from pathlib import Path


def generate_completion_certificate(username, session_id, completion_date, total_characters=6):
    """Generate a completion certificate PDF"""
    buffer = io.BytesIO()
    
    # Create PDF
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set colors
    primary_color = colors.HexColor('#667eea')
    secondary_color = colors.HexColor('#764ba2')
    
    # Add border
    pdf.setStrokeColor(primary_color)
    pdf.setLineWidth(3)
    pdf.rect(0.5*inch, 0.5*inch, width-1*inch, height-1*inch)
    
    # Inner border
    pdf.setStrokeColor(secondary_color)
    pdf.setLineWidth(1)
    pdf.rect(0.6*inch, 0.6*inch, width-1.2*inch, height-1.2*inch)
    
    # Title
    pdf.setFont("Helvetica-Bold", 36)
    pdf.setFillColor(primary_color)
    pdf.drawCentredString(width/2, height-1.5*inch, "CERTIFICATE")
    pdf.drawCentredString(width/2, height-2*inch, "OF COMPLETION")
    
    # Subtitle
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width/2, height-2.5*inch, "This is to certify that")
    
    # Name
    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(secondary_color)
    pdf.drawCentredString(width/2, height-3.2*inch, username.upper())
    
    # Achievement text
    pdf.setFont("Helvetica", 14)
    pdf.setFillColor(colors.black)
    text1 = "has successfully completed the"
    text2 = "'Mahabharata And You' Self Assessment"
    text3 = f"covering all {total_characters} character archetypes"
    
    pdf.drawCentredString(width/2, height-3.9*inch, text1)
    pdf.drawCentredString(width/2, height-4.3*inch, text2)
    pdf.drawCentredString(width/2, height-4.7*inch, text3)
    
    # Quote
    pdf.setFont("Helvetica-Oblique", 12)
    pdf.setFillColor(primary_color)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width/2, height-5.9*inch, "Excellence in action is Yoga")
    
    # Date and Session ID
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)
    pdf.drawString(1.5*inch, 2*inch, f"Date: {completion_date}")
    pdf.drawString(1.5*inch, 1.7*inch, f"Session ID: {session_id}")
    
    # Signature line
    pdf.setLineWidth(1)
    pdf.setStrokeColor(colors.black)
    pdf.line(width-3.5*inch, 2*inch, width-1.5*inch, 2*inch)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width-2.5*inch, 1.8*inch, "Authorized Signature")
    
    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.grey)
    pdf.drawCentredString(width/2, 0.8*inch, "Mahabharata Character Assessment Platform")
    pdf.drawCentredString(width/2, 0.6*inch, "Discover your professional archetype based on Mahabharata characters")
    
    pdf.save()
    buffer.seek(0)
    return buffer


def generate_analysis_report(username, session_id, responses, avg_rating, strongest_character):
    """Generate detailed analysis report card PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=0.75*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    # Title
    title = Paragraph("📊 CHARACTER ASSESSMENT REPORT", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))
    
    # User Info
    user_info_data = [
        ['Name:', username],
        ['Session ID:', session_id],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
        ['Characters Assessed:', str(len(responses))],
        ['Average Rating:', f"{avg_rating:.1f}/10"],
        ['Strongest Archetype:', strongest_character]
    ]
    
    user_info_table = Table(user_info_data, colWidths=[2*inch, 4*inch])
    user_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(user_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Individual Character Analysis
    for idx, response in enumerate(responses):
        # Character heading
        char_heading = Paragraph(f"🎭 {response['character_name']}", heading_style)
        elements.append(char_heading)
        
        # Rating
        rating_text = Paragraph(f"<b>Overall Rating:</b> {response['analysis']['overall_rating']:.1f}/10", normal_style)
        elements.append(rating_text)
        elements.append(Spacer(1, 0.1*inch))
        
        # Strengths
        strengths_text = "<b>💪 Strengths:</b><br/>" + "<br/>".join([f"• {s}" for s in response['analysis'].get('strengths', [])])
        elements.append(Paragraph(strengths_text, normal_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Areas for Improvement
        improvements_text = "<b>🎯 Areas for Improvement:</b><br/>" + "<br/>".join([f"• {a}" for a in response['analysis'].get('areas_for_improvement', [])])
        elements.append(Paragraph(improvements_text, normal_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Recommendations
        recommendations_text = "<b>💡 Recommendations:</b><br/>" + "<br/>".join([f"• {r}" for r in response['analysis'].get('recommendations', [])])
        elements.append(Paragraph(recommendations_text, normal_style))
        
        # Add page break except for last character
        if idx < len(responses) - 1:
            elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer