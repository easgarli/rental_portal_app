from docxtpl import DocxTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from datetime import datetime

def generate_contract(application):
    # Load the template
    doc = DocxTemplate("templates/contract_template.docx")
    
    # Prepare contract data according to contract_instructions.md
    context = {
        'ContractNo': str(application.id),
        'ContractDate': datetime.now().strftime("%Y-%m-%d"),
        
        # Landlord details
        'LandlordFirstName': application.contract_data.get('landlord_first_name'),
        'LandlordLastName': application.contract_data.get('landlord_last_name'),
        'LandlordFatherName': application.contract_data.get('landlord_father_name'),
        'LandlordID': application.contract_data.get('landlord_id'),
        'LandlordFIN': application.contract_data.get('landlord_fin'),
        'LandlordBirthPlace': application.contract_data.get('landlord_birth_place'),
        'LandlordBirthDate': application.contract_data.get('landlord_birth_date'),
        'LandlordAddress': application.contract_data.get('landlord_address'),
        
        # Tenant details
        'TenantFirstName': application.contract_data.get('tenant_first_name'),
        'TenantLastName': application.contract_data.get('tenant_last_name'),
        'TenantFatherName': application.contract_data.get('tenant_father_name'),
        'TenantID': application.contract_data.get('tenant_id'),
        'TenantFIN': application.contract_data.get('tenant_fin'),
        'TenantBirthPlace': application.contract_data.get('tenant_birth_place'),
        'TenantBirthDate': application.contract_data.get('tenant_birth_date'),
        'TenantAddress': application.contract_data.get('tenant_address'),
        
        # Property details
        'PropertyRegistryNumber': application.contract_data.get('property_registry_number'),
        'PropertyAddress': application.property.address,
        'PropertyArea': application.contract_data.get('property_area'),
        
        # Contract terms
        'RentAmount': str(application.property.monthly_rent),
        'ContractTerm': application.contract_data.get('contract_term')
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
    c.drawString(50, y, "RENTAL CONTRACT")
    y -= 30
    
    # Contract details
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Contract No: {context['ContractNo']}")
    y -= 20
    c.drawString(50, y, f"Date: {context['ContractDate']}")
    y -= 40
    
    # Landlord details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Landlord Information")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Landlord')}.items():
        c.drawString(50, y, f"{key[8:]}: {value}")
        y -= 20
    
    y -= 20
    
    # Tenant details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Tenant Information")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Tenant')}.items():
        c.drawString(50, y, f"{key[6:]}: {value}")
        y -= 20
    
    y -= 20
    
    # Property details
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Property Information")
    y -= 20
    c.setFont("Helvetica", 12)
    for key, value in {k: v for k, v in context.items() if k.startswith('Property')}.items():
        c.drawString(50, y, f"{key[8:]}: {value}")
        y -= 20
    
    # Signatures
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Signatures:")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Landlord: {application.landlord_signature}")
    y -= 20
    c.drawString(50, y, f"Tenant: {application.tenant_signature}")
    
    c.save()
    
    return pdf_filename 