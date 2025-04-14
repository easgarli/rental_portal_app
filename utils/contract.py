from docxtpl import DocxTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime, UTC
from flask import current_app

def generate_contract(application):
    """Generate a rental contract for the application"""
    try:
        # Check if both parties have provided their information
        if not application.tenant.contract_info or not application.rental_property.landlord.contract_info:
            raise ValueError("Missing required contract information")
        
        # Generate contract content
        contract_content = generate_contract_content(application)
        
        # Update application with contract details
        application.contract_content = contract_content
        application.contract_status = 'pending_signatures'  # Set status to pending signatures
        application.contract_generated_at = datetime.now(UTC)
        
        return contract_content
        
    except Exception as e:
        current_app.logger.error(f"Error generating contract: {str(e)}")
        raise

def generate_contract_content(application):
    # Load the template
    doc = DocxTemplate("templates/contract_template.docx")
    
    # Get tenant and landlord info through relationships
    tenant_info = application.tenant.contract_info[0] if application.tenant.contract_info else None
    landlord_info = application.rental_property.landlord.contract_info[0] if application.rental_property.landlord.contract_info else None
    property_info = application.rental_property
    
    # Check if required information is missing
    if not landlord_info:
        raise ValueError("Kirayə verənin məlumatları tamamlanmayıb")
    if not tenant_info:
        raise ValueError("Kirayəçinin məlumatları tamamlanmayıb")
    
    # Prepare contract data
    context = {
        'ContractNo': str(application.id),
        'ContractDate': datetime.now().strftime("%Y-%m-%d"),
        
        # Landlord details
        'LandlordFirstName': landlord_info.first_name if landlord_info else None,
        'LandlordLastName': landlord_info.last_name if landlord_info else None,
        'LandlordFatherName': landlord_info.father_name if landlord_info else None,
        'LandlordID': landlord_info.id_number if landlord_info else None,
        'LandlordFIN': landlord_info.fin if landlord_info else None,
        'LandlordBirthPlace': landlord_info.birth_place if landlord_info else None,
        'LandlordBirthDate': landlord_info.birth_date.strftime("%Y-%m-%d") if landlord_info and landlord_info.birth_date else None,
        
        # Tenant details
        'TenantFirstName': tenant_info.first_name if tenant_info else None,
        'TenantLastName': tenant_info.last_name if tenant_info else None,
        'TenantFatherName': tenant_info.father_name if tenant_info else None,
        'TenantID': tenant_info.id_number if tenant_info else None,
        'TenantFIN': tenant_info.fin if tenant_info else None,
        'TenantBirthPlace': tenant_info.birth_place if tenant_info else None,
        'TenantBirthDate': tenant_info.birth_date.strftime("%Y-%m-%d") if tenant_info and tenant_info.birth_date else None,
        'TenantAddress': tenant_info.address if tenant_info else None,
        
        # Property details
        'PropertyRegistryNumber': property_info.registry_number,
        'PropertyAddress': property_info.address,
        'PropertyArea': property_info.area,
        'PropertyRent': property_info.monthly_rent,
        'PropertyContractTerm': property_info.contract_term,
        
        # Signatures
        'LandlordSignature': application.landlord_signature,
        'TenantSignature': application.tenant_signature
    }
    
    # Create output directory if it doesn't exist
    os.makedirs('static/contracts', exist_ok=True)
    
    # Generate PDF filename
    pdf_filename = f"contract_{application.id}.pdf"
    pdf_path = os.path.join('static/contracts', pdf_filename)
    
    # Create PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Add content to PDF
    y = 750  # Starting y position
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "KİRAYƏ MÜQAVİLƏSİ")
    y -= 30
    
    # Contract details
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Müqavilə №: {context['ContractNo']}")
    y -= 20
    c.drawString(50, y, f"Tarix: {context['ContractDate']}")
    y -= 40
    
    # Landlord details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Kirayə verənin məlumatları")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Landlord')}.items():
        if value:  # Only draw if value exists
            c.drawString(50, y, f"{key[8:]}: {value}")
            y -= 20
    
    y -= 20
    
    # Tenant details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "İstifadəçi məlumatları")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Tenant')}.items():
        if value:  # Only draw if value exists
            c.drawString(50, y, f"{key[6:]}: {value}")
            y -= 20
    
    y -= 20
    
    # Property details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Əmlak məlumatları")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Property')}.items():
        if value:  # Only draw if value exists
            c.drawString(50, y, f"{key[8:]}: {value}")
            y -= 20
    
    # Save the PDF
    c.save()
    
    return pdf_filename 