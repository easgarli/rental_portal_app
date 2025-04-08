from flask import Blueprint, jsonify, request, render_template, send_from_directory, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, RentalApplication, Property, User, TenantScore, UserContractInfo
from utils.contract import generate_contract
from datetime import datetime

applications_bp = Blueprint('applications', __name__)

@applications_bp.route('/apply/<property_id>', methods=['POST'])
@login_required
def apply_for_property(property_id):
    if current_user.role != 'tenant':
        return jsonify({'error': 'Only tenants can apply for properties'}), 403
    
    # Check if tenant already has contract info
    has_contract_info = UserContractInfo.query.filter_by(user_id=current_user.id).first() is not None
    
    # Create application
    application = RentalApplication(
        tenant_id=current_user.id,
        property_id=property_id
    )
    db.session.add(application)
    db.session.commit()
    
    if not has_contract_info:
        # If tenant hasn't provided their info yet, redirect to info form
        return jsonify({
            'message': 'Please provide your information to complete the application',
            'next_step': 'tenant_info',
            'application_id': application.id
        })
    else:
        # If tenant already has info stored, application is complete
        return jsonify({
            'message': 'Application submitted successfully',
            'next_step': 'view_applications'
        })

@applications_bp.route('/api/applications/tenant', methods=['GET'])
@login_required
def get_tenant_applications():
    """Get all applications for the current tenant"""
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
        
    applications = RentalApplication.query.filter_by(tenant_id=current_user.id)\
        .order_by(RentalApplication.created_at.desc()).all()
    
    return jsonify([{
        'id': app.id,
        'status': app.status,
        'created_at': app.created_at.isoformat(),
        'contract_status': app.contract_status or 'none',
        'property': {
            'id': app.property.id,
            'title': app.property.title,
            'address': app.property.address,
            'monthly_rent': float(app.property.monthly_rent),
            'landlord': {
                'id': app.property.landlord.id,
                'name': app.property.landlord.name
            }
        }
    } for app in applications])

@applications_bp.route('/applications/landlord', methods=['GET'])
@login_required
def get_landlord_applications():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
        
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    applications = RentalApplication.query.filter(
        RentalApplication.property_id.in_(property_ids)
    ).all()
    
    return jsonify([{
        'id': app.id,
        'status': app.status,
        'created_at': app.created_at.isoformat(),
        'contract_status': app.contract_status or 'none',
        'tenant_signature': bool(app.tenant_signature),
        'landlord_signature': bool(app.landlord_signature),
        'tenant': {
            'id': app.tenant.id,
            'name': app.tenant.name
        },
        'property': {
            'id': app.property.id,
            'title': app.property.title
        }
    } for app in applications])

@applications_bp.route('/applications/<application_id>/approve', methods=['POST'])
@login_required
def approve_application(application_id):
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
        
    application = RentalApplication.query.get_or_404(application_id)
    
    # Verify this landlord owns the property
    if application.property.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        application.status = 'approved'
        # Set contract status based on whether tenant info exists
        tenant_info = UserContractInfo.query.filter_by(user_id=application.tenant_id).first()
        application.contract_status = 'draft' if tenant_info else 'none'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Müraciət təsdiqləndi',
            'application': {
                'id': application.id,
                'status': application.status,
                'contract_status': application.contract_status
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error approving application: {str(e)}")  # For debugging
        return jsonify({
            'success': False,
            'message': 'Status yeniləmək mümkün olmadı'
        }), 500

@applications_bp.route('/applications/<application_id>/contract', methods=['GET', 'POST'])
@login_required
def manage_contract(application_id):
    application = RentalApplication.query.get_or_404(application_id)
    
    # Check if user has filled out their information
    if current_user.role == 'landlord' and not current_user.contract_info:
        flash('Zəhmət olmasa müqavilə üçün məlumatlarınızı doldurun', 'warning')
        return redirect(url_for('applications.landlord_info_form', application_id=application_id))
    
    if current_user.role == 'tenant' and not current_user.contract_info:
        flash('Zəhmət olmasa müqavilə üçün məlumatlarınızı doldurun', 'warning')
        return redirect(url_for('applications.tenant_info_form', application_id=application_id))

    if request.method == 'GET':
        contract_info = None
        property_info = None
        
        if current_user.role == 'landlord':
            contract_info = application.property.landlord.contract_info[0]
            property_info = application.property
        elif current_user.role == 'tenant':
            contract_info = application.tenant.contract_info[0]
        
        return render_template('applications/contract_form.html',
                           application=application,
                           contract_info=contract_info,
                           property_info=property_info if current_user.role == 'landlord' else None,
                           tenant_info=contract_info,
                           landlord_info=application.property.landlord.contract_info[0] if application.property.landlord.contract_info else None)

    # Handle POST request for contract signing
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if current_user.role == 'landlord':
                application.landlord_signature = data.get('signature')
            else:
                application.tenant_signature = data.get('signature')
            
            if application.landlord_signature and application.tenant_signature:
                application.contract_status = 'completed'
                
                try:
                    contract_filename = generate_contract(application)
                    application.contract_data = {'filename': contract_filename}
                except ValueError as e:
                    return jsonify({'success': False, 'message': str(e)}), 400
                except Exception as e:
                    print(f"Error generating contract: {e}")
                    return jsonify({'success': False, 'message': 'Müqavilə yaratmaq mümkün olmadı'}), 500
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Error handling signature: {e}")
            return jsonify({'success': False, 'message': 'Müqaviləni imzalamaq mümkün olmadı'}), 500

@applications_bp.route('/applications/<application_id>/contract/download')
@login_required
def download_contract(application_id):
    application = RentalApplication.query.get_or_404(application_id)
    if not application.contract_status == 'completed':
        abort(400, 'Contract is not yet completed')
    
    filename = application.contract_data.get('filename')
    if not filename:
        abort(404, 'Contract file not found')
    
    return send_from_directory('static/contracts', filename)

@applications_bp.route('/applications/<application_id>/contract/details', methods=['POST'])
@login_required
def save_contract_details(application_id):
    application = RentalApplication.query.get_or_404(application_id)
    data = request.get_json()
    
    # Get existing contract data or initialize empty dict
    contract_data = application.contract_data or {}
    
    if current_user.role == 'landlord':
        # Update landlord and property details
        contract_data.update({
            'landlord_first_name': data.get('landlord_first_name'),
            'landlord_last_name': data.get('landlord_last_name'),
            'landlord_father_name': data.get('landlord_father_name'),
            'landlord_id': data.get('landlord_id'),
            'landlord_fin': data.get('landlord_fin'),
            'landlord_birth_place': data.get('landlord_birth_place'),
            'landlord_birth_date': data.get('landlord_birth_date'),
            'landlord_address': data.get('landlord_address'),
            'property_registry_number': data.get('property_registry_number'),
            'property_area': data.get('property_area'),
            'contract_term': data.get('contract_term')
        })
    elif current_user.role == 'tenant':
        # Update tenant details only
        contract_data.update({
            'tenant_first_name': data.get('tenant_first_name'),
            'tenant_last_name': data.get('tenant_last_name'),
            'tenant_father_name': data.get('tenant_father_name'),
            'tenant_id': data.get('tenant_id'),
            'tenant_fin': data.get('tenant_fin'),
            'tenant_birth_place': data.get('tenant_birth_place'),
            'tenant_birth_date': data.get('tenant_birth_date'),
            'tenant_address': data.get('tenant_address')
        })
    
    application.contract_data = contract_data
    
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Contract details saved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@applications_bp.route('/applications/<application_id>/tenant-info', methods=['GET', 'POST'])
@login_required
def manage_tenant_info(application_id):
    # Handle the case when creating new tenant info without an application
    if application_id == 'new':
        application = None
    else:
        application = RentalApplication.query.get_or_404(application_id)
        if application.tenant_id != current_user.id:
            abort(403)

    if request.method == 'POST':
        data = request.get_json()
        
        # Get or create contract info
        contract_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
        if not contract_info:
            contract_info = UserContractInfo(user_id=current_user.id)
            db.session.add(contract_info)
        
        # Update contract info
        contract_info.first_name = data.get('first_name')
        contract_info.last_name = data.get('last_name')
        contract_info.father_name = data.get('father_name')
        contract_info.id_number = data.get('id_number')
        contract_info.fin = data.get('fin')
        contract_info.birth_place = data.get('birth_place')
        contract_info.birth_date = datetime.strptime(data.get('birth_date'), '%Y-%m-%d').date()
        contract_info.address = data.get('address')
        
        try:
            db.session.commit()
            if application:
                return jsonify({'success': True, 'redirect_url': url_for('applications.manage_contract', application_id=application.id)})
            else:
                return jsonify({'success': True, 'redirect_url': url_for('dashboard')})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

    return render_template('applications/tenant_info_form.html',
                         contract_info=current_user.contract_info[0] if current_user.contract_info else None,
                         application=application if application_id != 'new' else None)

@applications_bp.route('/applications/<application_id>/landlord-info', methods=['GET', 'POST'])
@login_required
def manage_landlord_info(application_id):
    application = RentalApplication.query.get_or_404(application_id)
    
    if current_user.role != 'landlord' or current_user.id != application.property.landlord_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Get or create user contract info
        contract_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
        if not contract_info:
            contract_info = UserContractInfo(user_id=current_user.id)
        
        # Update contract info
        for field in ['first_name', 'last_name', 'father_name', 'id_number', 
                     'fin', 'birth_place', 'birth_date', 'address']:
            setattr(contract_info, field, data.get(field))
        
        db.session.add(contract_info)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contract information saved'})
    
    # GET request - return existing info if available
    contract_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
    return render_template('applications/landlord_info_form.html', 
                         contract_info=contract_info,
                         application=application,
                         title="Mülk sahibinin məlumatları")

@applications_bp.route('/applications/<application_id>/reject', methods=['POST'])
@login_required
def reject_application(application_id):
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
        
    application = RentalApplication.query.get_or_404(application_id)
    
    # Verify this landlord owns the property
    if application.property.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        application.status = 'rejected'
        application.contract_status = 'none'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Müraciət rədd edildi',
            'application': {
                'id': application.id,
                'status': application.status,
                'contract_status': application.contract_status
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error rejecting application: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Status yeniləmək mümkün olmadı'
        }), 500

@applications_bp.route('/applications/<application_id>/property-info', methods=['GET', 'POST'])
@login_required
def manage_property_info(application_id):
    application = RentalApplication.query.get_or_404(application_id)
    
    if current_user.role != 'landlord' or current_user.id != application.property.landlord_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Update property info
        property = application.property
        property.registry_number = data.get('registry_number')
        property.area = data.get('area')
        property.contract_term = data.get('contract_term')
        
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Əmlak məlumatları yadda saxlanıldı'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    # GET request - return form
    return render_template('applications/property_info_form.html',
                         application=application,
                         property=application.property,
                         title="Əmlak məlumatları") 