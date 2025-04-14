from flask import Blueprint, jsonify, request, render_template, send_from_directory, abort, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, RentalApplication, Property, User, TenantScore, UserContractInfo
import utils.contract
from datetime import datetime, UTC
from flask_wtf import FlaskForm
from wtforms import StringField, DateField
from wtforms.validators import DataRequired

applications_bp = Blueprint('applications', __name__)

class ContractInfoForm(FlaskForm):
    pass  # We only need this for CSRF protection

class LandlordInfoForm(FlaskForm):
    first_name = StringField('Ad', validators=[DataRequired()])
    last_name = StringField('Soyad', validators=[DataRequired()])
    father_name = StringField('Ata adı', validators=[DataRequired()])
    id_number = StringField('Şəxsiyyət vəsiqəsinin nömrəsi', validators=[DataRequired()])
    fin = StringField('FİN', validators=[DataRequired()])
    birth_place = StringField('Doğum yeri', validators=[DataRequired()])
    birth_date = DateField('Doğum tarixi', validators=[DataRequired()])
    address = StringField('Qeydiyyat ünvanı', validators=[DataRequired()])

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
    if application.rental_property.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        application.status = 'approved'
        # Always set contract status to 'draft' when approving
        application.contract_status = 'draft'
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
    """Manage contract creation process"""
    application = RentalApplication.query.get_or_404(application_id)
    
    # Verify authorization
    if current_user.role == 'landlord' and application.rental_property.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if current_user.role == 'tenant' and application.tenant_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Handle POST request for signing
    if request.method == 'POST':
        try:
            # Check if contract is ready for signatures
            if application.contract_status not in ['pending_signatures', 'draft']:
                return jsonify({'error': 'Müqavilə imzalanmağa hazır deyil'}), 400
            
            # Add signature
            if current_user.role == 'tenant':
                if application.tenant_signature:
                    return jsonify({'error': 'Müqavilə artıq imzalanıb'}), 400
                application.tenant_signature = datetime.now(UTC)
                application.contract_status = 'pending_signatures'
            else:  # landlord
                if application.landlord_signature:
                    return jsonify({'error': 'Müqavilə artıq imzalanıb'}), 400
                application.landlord_signature = datetime.now(UTC)
                application.contract_status = 'pending_signatures'
            
            # If both parties have signed, activate the contract
            if application.tenant_signature and application.landlord_signature:
                application.contract_status = 'active'
                application.rental_property.status = 'rented'
            
            db.session.commit()
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error signing contract: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # GET request - show contract form
    # Check if landlord info exists
    landlord = User.query.get(application.rental_property.landlord_id)
    landlord_info = UserContractInfo.query.filter_by(user_id=landlord.id).first()
    
    if not landlord_info:
        if current_user.role == 'landlord':
            return redirect(url_for('applications.manage_landlord_info', application_id=application_id))
        else:
            flash('Mülk sahibi məlumatları gözlənilir', 'warning')
            return redirect(url_for('tenant.applications'))
    
    # Check if tenant info exists
    tenant_info = UserContractInfo.query.filter_by(user_id=application.tenant_id).first()
    if not tenant_info:
        if current_user.role == 'tenant':
            return redirect(url_for('applications.manage_tenant_info', application_id=application_id))
        else:
            flash('İcarədar məlumatları gözlənilir', 'warning')
            return redirect(url_for('landlord.applications'))
    
    # Check if property info is complete
    property = application.rental_property
    if not all([property.registry_number, property.area, property.contract_term]):
        if current_user.role == 'landlord':
            return redirect(url_for('applications.manage_property_info', application_id=application_id))
        else:
            flash('Əmlak məlumatları gözlənilir', 'warning')
            return redirect(url_for('tenant.applications'))
    
    # If all info is complete, show contract
    return render_template('applications/contract_form.html',
                         application=application,
                         landlord_info=landlord_info,
                         tenant_info=tenant_info)

@applications_bp.route('/applications/<application_id>/contract/download')
@login_required
def download_contract(application_id):
    """Download the contract document"""
    application = RentalApplication.query.get_or_404(application_id)
    
    # Check permissions
    if (current_user.role == 'tenant' and application.tenant_id != current_user.id) or \
       (current_user.role == 'landlord' and application.rental_property.landlord_id != current_user.id):
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('dashboard'))
    
    if not application.contract_data or 'filename' not in application.contract_data:
        flash('Müqavilə faylı tapılmadı', 'danger')
        return redirect(url_for('tenant.contracts' if current_user.role == 'tenant' else 'landlord.contracts'))
    
    return send_from_directory('static/contracts', application.contract_data['filename'], as_attachment=True)

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
    
    # Get the first (and should be only) contract info for the landlord
    contract_info = UserContractInfo.query.filter_by(
        user_id=application.rental_property.landlord_id
    ).first()
    
    if request.method == 'GET':
        return render_template(
            'applications/landlord_info.html',
            application=application,
            contract_info=contract_info
        )
    
    # Handle POST request...
    try:
        if not contract_info:
            contract_info = UserContractInfo(
                user_id=application.rental_property.landlord_id,
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                father_name=request.form['father_name'],
                id_number=request.form['id_number'],
                fin=request.form['fin'],
                birth_place=request.form['birth_place'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date(),
                address=request.form['address']
            )
            db.session.add(contract_info)
        else:
            # Update existing contract info
            contract_info.first_name = request.form['first_name']
            contract_info.last_name = request.form['last_name']
            contract_info.father_name = request.form['father_name']
            contract_info.id_number = request.form['id_number']
            contract_info.fin = request.form['fin']
            contract_info.birth_place = request.form['birth_place']
            contract_info.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
            contract_info.address = request.form['address']
        
        db.session.commit()
        flash('Məlumatlar uğurla yeniləndi', 'success')
        return redirect(url_for('applications.view_application', application_id=application_id))
        
    except Exception as e:
        db.session.rollback()
        flash('Xəta baş verdi', 'danger')
        current_app.logger.error(f"Error updating landlord contract info: {str(e)}")
        return redirect(url_for('applications.manage_landlord_info', application_id=application_id))

@applications_bp.route('/applications/<application_id>/reject', methods=['POST'])
@login_required
def reject_application(application_id):
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
        
    application = RentalApplication.query.get_or_404(application_id)
    
    # Verify this landlord owns the property
    if application.rental_property.landlord_id != current_user.id:
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
    
    if current_user.role != 'landlord' or current_user.id != application.rental_property.landlord_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Update property info
        property = application.rental_property
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
                         property=application.rental_property,
                         title="Əmlak məlumatları")

@applications_bp.route('/api/applications', methods=['POST'])
@login_required
def create_application():
    """Create a new rental application"""
    if current_user.role != 'tenant':
        return jsonify({'error': 'Yalnız icarədarlar müraciət edə bilər'}), 403
    
    try:
        data = request.get_json()
        property_id = data.get('property_id')
        
        # Check if property exists
        property = Property.query.get_or_404(property_id)
        
        # Check if property is available
        if property.status != 'available':
            return jsonify({'error': 'Bu əmlak hal-hazırda boş deyil'}), 400
        
        # Check if application already exists
        existing_application = RentalApplication.query.filter_by(
            tenant_id=current_user.id,
            property_id=property_id,
            status='pending'
        ).first()
        
        if existing_application:
            return jsonify({'error': 'Bu əmlak üçün artıq müraciət etmisiniz'}), 400
        
        # Create new application
        application = RentalApplication(
            tenant_id=current_user.id,
            property_id=property_id,
            status='pending',
            created_at=datetime.now(UTC)
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Müraciətiniz qeydə alındı',
            'application_id': application.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/applications/<application_id>', methods=['GET'])
@login_required
def view_application(application_id):
    """View application details"""
    application = RentalApplication.query.get_or_404(application_id)
    
    # Check if user has permission to view this application
    if (current_user.role == 'tenant' and application.tenant_id != current_user.id) or \
       (current_user.role == 'landlord' and application.rental_property.landlord_id != current_user.id):
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get contract info status
    landlord_info = application.rental_property.landlord.contract_info[0] if application.rental_property.landlord.contract_info else None
    tenant_info = application.tenant.contract_info[0] if application.tenant.contract_info else None
    property_info = application.rental_property
    
    # Calculate contract progress
    progress_steps = 0
    total_steps = 3  # landlord info, tenant info, property info
    
    if landlord_info:
        progress_steps += 1
    if tenant_info:
        progress_steps += 1
    if property_info.registry_number and property_info.area and property_info.contract_term:
        progress_steps += 1
        
    contract_progress = int((progress_steps / total_steps) * 100)
    contract_ready = progress_steps == total_steps
    
    return render_template('applications/view_application.html',
                         application=application,
                         landlord_info=landlord_info,
                         tenant_info=tenant_info,
                         property_info=property_info,
                         contract_progress=contract_progress,
                         contract_ready=contract_ready)

@applications_bp.route('/applications/<application_id>/generate-contract')
@login_required
def generate_contract(application_id):
    """Generate contract document for an application"""
    application = RentalApplication.query.get_or_404(application_id)
    
    try:
        # Generate contract using the utility function
        filename = utils.contract.generate_contract(application)
        
        # Update application status
        application.contract_status = 'pending_signatures'
        application.contract_data = {'filename': filename}
        db.session.commit()
        
        # Return the generated file
        return send_from_directory('static/contracts', filename, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"Error generating contract: {str(e)}")
        flash('Müqavilə hazırlanması zamanı xəta baş verdi', 'danger')
        return redirect(url_for('applications.view_application', application_id=application_id))

@applications_bp.route('/applications/<application_id>/contract/sign', methods=['POST'])
@login_required
def sign_contract(application_id):
    """Sign the contract"""
    try:
        application = RentalApplication.query.get_or_404(application_id)
        current_app.logger.info(f"Attempting to sign contract {application_id} for user {current_user.id}")
        current_app.logger.info(f"Contract status: {application.contract_status}")
        current_app.logger.info(f"Tenant signature: {application.tenant_signature}")
        current_app.logger.info(f"Landlord signature: {application.landlord_signature}")
        
        # Check permissions
        if (current_user.role == 'tenant' and application.tenant_id != current_user.id) or \
           (current_user.role == 'landlord' and application.rental_property.landlord_id != current_user.id):
            current_app.logger.warning(f"Unauthorized attempt to sign contract {application_id} by user {current_user.id}")
            return jsonify({'error': 'Bu əməliyyat üçün icazəniz yoxdur'}), 403
        
        # Check if contract is ready for signatures
        if application.contract_status not in ['pending_signatures', 'draft']:
            current_app.logger.warning(f"Contract {application_id} not ready for signatures. Status: {application.contract_status}")
            return jsonify({'error': 'Müqavilə imzalanmağa hazır deyil'}), 400
        
        # Check if all required information is complete
        if not application.tenant.contract_info:
            current_app.logger.warning(f"Tenant info missing for contract {application_id}")
            return jsonify({'error': 'İcarəçi məlumatları tamamlanmayıb'}), 400
            
        if not application.rental_property.landlord.contract_info:
            current_app.logger.warning(f"Landlord info missing for contract {application_id}")
            return jsonify({'error': 'Mülk sahibi məlumatları tamamlanmayıb'}), 400
        
        # Check if property info is complete
        property_info = {
            'registry_number': application.rental_property.registry_number,
            'area': application.rental_property.area,
            'contract_term': application.rental_property.contract_term
        }
        missing_property_info = [k for k, v in property_info.items() if not v]
        if missing_property_info:
            current_app.logger.warning(f"Property info incomplete for contract {application_id}. Missing: {missing_property_info}")
            return jsonify({'error': 'Əmlak məlumatları tamamlanmayıb'}), 400
        
        # Add signature
        if current_user.role == 'tenant':
            if application.tenant_signature:
                current_app.logger.warning(f"Tenant already signed contract {application_id}")
                return jsonify({'error': 'Müqavilə artıq imzalanıb'}), 400
            application.tenant_signature = datetime.now(UTC)
            application.contract_status = 'pending_signatures'  # Ensure status is set
            current_app.logger.info(f"Tenant signed contract {application_id}")
        else:  # landlord
            if application.landlord_signature:
                current_app.logger.warning(f"Landlord already signed contract {application_id}")
                return jsonify({'error': 'Müqavilə artıq imzalanıb'}), 400
            application.landlord_signature = datetime.now(UTC)
            application.contract_status = 'pending_signatures'  # Ensure status is set
            current_app.logger.info(f"Landlord signed contract {application_id}")
        
        # If both parties have signed, activate the contract
        if application.tenant_signature and application.landlord_signature:
            application.contract_status = 'active'
            application.rental_property.status = 'rented'
            current_app.logger.info(f"Contract {application_id} activated")
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error while signing contract {application_id}: {str(e)}")
            return jsonify({'error': 'Verilənlər bazası xətası'}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error signing contract {application_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@applications_bp.route('/applications/new/landlord-info', methods=['GET', 'POST'])
@login_required
def new_landlord_info():
    """Create new landlord contract info"""
    if current_user.role != 'landlord':
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('dashboard'))

    form = ContractInfoForm()
    
    # Check if landlord already has contract info
    existing_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
    if existing_info:
        return redirect(url_for('landlord.dashboard'))

    if request.method == 'POST' and form.validate():
        try:
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'father_name', 'id_number', 
                             'fin', 'birth_place', 'birth_date', 'address']
            
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field} sahəsi tələb olunur', 'danger')
                    return render_template('applications/landlord_info.html', 
                                        contract_info=None, 
                                        application=None,
                                        title="Yeni müqavilə məlumatları",
                                        form=form)

            contract_info = UserContractInfo(
                user_id=current_user.id,
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                father_name=request.form['father_name'],
                id_number=request.form['id_number'],
                fin=request.form['fin'],
                birth_place=request.form['birth_place'],
                birth_date=datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date(),
                address=request.form['address']
            )
            
            db.session.add(contract_info)
            db.session.commit()
            
            flash('Məlumatlar uğurla yadda saxlanıldı', 'success')
            return redirect(url_for('landlord.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving landlord contract info: {str(e)}")
            flash('Xəta baş verdi: ' + str(e), 'danger')
            return render_template('applications/landlord_info.html', 
                                contract_info=None, 
                                application=None,
                                title="Yeni müqavilə məlumatları",
                                form=form)
            
    return render_template('applications/landlord_info.html', 
                         contract_info=None, 
                         application=None,
                         title="Yeni müqavilə məlumatları",
                         form=form) 