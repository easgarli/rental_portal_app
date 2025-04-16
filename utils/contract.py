from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch
from reportlab.lib.colors import black
import os
from datetime import datetime, UTC
from flask import current_app
import textwrap

def generate_contract(application):
    """Generate a rental contract for an application"""
    try:
        # Get all required data before generating the contract
        tenant_info = application.tenant.contract_info[0] if application.tenant.contract_info else None
        landlord_info = application.rental_property.landlord.contract_info[0] if application.rental_property.landlord.contract_info else None
        property_info = application.rental_property
        
        # Validate all required information
        if not tenant_info or not landlord_info:
            raise ValueError("Contract information is incomplete")
            
        if not all([property_info.registry_number, property_info.area, property_info.contract_term]):
            raise ValueError("Property information is incomplete")
        
        # Generate contract content
        contract_content = generate_contract_content(application)
        
        # Create PDF document
        filename = f"contract_{application.id}.pdf"
        filepath = os.path.join(current_app.static_folder, 'contracts', filename)
        
        # Ensure contracts directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add contract content
        story.append(Paragraph("İcarə Müqaviləsi", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Add contract details
        story.append(Paragraph(contract_content, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Update application with contract details
        application.contract_data = {
            'filename': filename,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return filename
        
    except Exception as e:
        current_app.logger.error(f"Error generating contract: {str(e)}")
        raise

def generate_contract_content(application):
    """Generate contract content from template and convert to PDF"""
    try:
        # Get tenant and landlord info through relationships
        tenant_info = application.tenant.contract_info[0] if application.tenant.contract_info else None
        landlord_info = application.rental_property.landlord.contract_info[0] if application.rental_property.landlord.contract_info else None
        property_info = application.rental_property
        
        # Check if required information is missing
        if not landlord_info:
            raise ValueError("Landlord information is incomplete")
        if not tenant_info:
            raise ValueError("Tenant information is incomplete")
        
        # Prepare contract data
        context = {
            'ContractNo': str(application.id),
            'ContractDate': datetime.now().strftime("%Y-%m-%d"),
            'LandlordFirstName': landlord_info.first_name,
            'LandlordLastName': landlord_info.last_name,
            'LandlordFatherName': landlord_info.father_name,
            'LandlordID': landlord_info.id_number,
            'LandlordFIN': landlord_info.fin,
            'LandlordBirthPlace': landlord_info.birth_place,
            'LandlordBirthDate': landlord_info.birth_date.strftime("%Y-%m-%d"),
            'LandlordAddress': landlord_info.address,
            'TenantFirstName': tenant_info.first_name,
            'TenantLastName': tenant_info.last_name,
            'TenantFatherName': tenant_info.father_name,
            'TenantID': tenant_info.id_number,
            'TenantFIN': tenant_info.fin,
            'TenantBirthPlace': tenant_info.birth_place,
            'TenantBirthDate': tenant_info.birth_date.strftime("%Y-%m-%d"),
            'TenantAddress': tenant_info.address,
            'PropertyRegistryNumber': property_info.registry_number,
            'PropertyAddress': property_info.address,
            'PropertyArea': property_info.area,
            'RentAmount': property_info.monthly_rent,
            'ContractTerm': property_info.contract_term
        }
        
        # Create output directory if it doesn't exist
        os.makedirs('static/contracts', exist_ok=True)
        
        # Generate PDF filename
        pdf_filename = f"contract_{application.id}.pdf"
        pdf_path = os.path.join('static/contracts', pdf_filename)
        
        # Register custom font
        font_path = os.path.join('static', 'fonts', 'DejaVuSans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='DejaVuSans',
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=12,
            leading=14,
            spaceAfter=12
        )
        
        # Read template
        template_path = os.path.join('templates', 'contracts', 'contract_template.txt')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace placeholders
        for key, value in context.items():
            template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))
        
        # Split content into paragraphs
        paragraphs = template_content.split('\n\n')
        
        # Create story (content) for PDF
        story = []
        
        # Add title
        story.append(Paragraph("YAŞAYIŞ SAHƏSİNİN KİRAYƏSİ HAQQINDA", title_style))
        story.append(Spacer(1, 20))
        
        # Add content paragraphs
        for para in paragraphs:
            if para.strip():  # Skip empty paragraphs
                # Wrap text to fit page width
                wrapped_text = textwrap.fill(para, width=80)
                story.append(Paragraph(wrapped_text, body_style))
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        return pdf_filename
        
    except Exception as e:
        current_app.logger.error(f"Error generating contract content: {str(e)}")
        raise 