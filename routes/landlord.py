from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Property, RentalApplication, UserContractInfo, Contract, Rating, User
from decorators import landlord_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField
from wtforms.validators import DataRequired, Optional

landlord_bp = Blueprint('landlord', __name__)

class PropertyForm(FlaskForm):
    title = StringField('Başlıq', validators=[DataRequired()])
    description = TextAreaField('Təsvir', validators=[Optional()])
    address = StringField('Ünvan', validators=[DataRequired()])
    monthly_rent = DecimalField('Aylıq kirayə', validators=[DataRequired()])
    available_from = DateField('Mövcudluq tarixi', validators=[DataRequired()])
    registry_number = StringField('Qeydiyyat nömrəsi', validators=[Optional()])
    area = DecimalField('Sahə', validators=[Optional()])
    contract_term = StringField('Müqavilə müddəti', validators=[Optional()])

@landlord_bp.route('/landlord/dashboard')
@login_required
@landlord_required
def dashboard():
    return render_template('landlord/dashboard.html')

@landlord_bp.route('/landlord/properties')
@login_required
@landlord_required
def properties():
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    return render_template('landlord/properties.html', properties=properties)

@landlord_bp.route('/landlord/add_property', methods=['GET', 'POST'])
@login_required
@landlord_required
def add_property():
    form = PropertyForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                property = Property(
                    landlord_id=current_user.id,
                    title=form.title.data,
                    description=form.description.data,
                    address=form.address.data,
                    monthly_rent=form.monthly_rent.data,
                    available_from=form.available_from.data,
                    registry_number=form.registry_number.data,
                    area=form.area.data,
                    contract_term=form.contract_term.data,
                    status='available'
                )
                db.session.add(property)
                db.session.commit()
                flash('Əmlak uğurla əlavə edildi', 'success')
                return redirect(url_for('landlord.properties'))
            except Exception as e:
                db.session.rollback()
                flash(f'Xəta baş verdi: {str(e)}', 'danger')
    return render_template('landlord/property_form.html', form=form)

@landlord_bp.route('/landlord/property/<property_id>/edit', methods=['GET', 'POST'])
@login_required
@landlord_required
def edit_property(property_id):
    property = Property.query.get_or_404(property_id)
    if property.landlord_id != current_user.id:
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('landlord.properties'))
    
    form = PropertyForm(obj=property)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                property.title = form.title.data
                property.description = form.description.data
                property.address = form.address.data
                property.monthly_rent = form.monthly_rent.data
                property.available_from = form.available_from.data
                property.registry_number = form.registry_number.data
                property.area = form.area.data
                property.contract_term = form.contract_term.data
                db.session.commit()
                flash('Əmlak uğurla yeniləndi', 'success')
                return redirect(url_for('landlord.properties'))
            except Exception as e:
                db.session.rollback()
                flash(f'Xəta baş verdi: {str(e)}', 'danger')
    return render_template('landlord/property_form.html', form=form, property=property)

@landlord_bp.route('/landlord/applications')
@login_required
@landlord_required
def applications():
    return render_template('landlord/applications.html')

@landlord_bp.route('/landlord/contracts')
@login_required
@landlord_required
def contracts():
    # Get all properties owned by the landlord
    properties = Property.query.filter_by(landlord_id=current_user.id).all()
    property_ids = [p.id for p in properties]
    
    # Get all applications for these properties
    applications = RentalApplication.query.filter(
        RentalApplication.property_id.in_(property_ids)
    ).all()
    
    # Get landlord's contract info
    landlord_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
    
    # Prepare contract data
    contracts = []
    for app in applications:
        # Check if property info is complete
        property = app.rental_property
        property_info_complete = all([
            property.registry_number,
            property.area,
            property.contract_term
        ])
        
        contracts.append({
            'id': app.id,
            'property': {
                'id': property.id,
                'title': property.title,
                'address': property.address,
                'info_complete': property_info_complete
            },
            'tenant': {
                'id': app.tenant.id,
                'name': app.tenant.name
            },
            'status': app.contract_status or 'draft',
            'landlord_info_complete': bool(landlord_info),
            'property_info_complete': property_info_complete,
            'landlord_signature': bool(app.landlord_signature),
            'tenant_signature': bool(app.tenant_signature),
            'created_at': app.created_at
        })
    
    return render_template('landlord/contracts.html', 
                         contracts=contracts,
                         landlord_info=landlord_info)

@landlord_bp.route('/landlord/ratings')
@login_required
@landlord_required
def ratings():
    return render_template('landlord/ratings.html')

@landlord_bp.route('/landlord/profile')
@login_required
@landlord_required
def profile():
    return render_template('landlord/profile.html')

@landlord_bp.route('/landlord/property/<property_id>/applications')
@login_required
@landlord_required
def property_applications(property_id):
    property = Property.query.get_or_404(property_id)
    if property.landlord_id != current_user.id:
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('landlord.properties'))
    
    applications = RentalApplication.query.filter_by(property_id=property_id).all()
    return render_template('landlord/property_applications.html', 
                         property=property,
                         applications=applications)

@landlord_bp.route('/landlord/property/<property_id>/contract')
@login_required
@landlord_required
def property_contract(property_id):
    """Show contract preparation page for a property"""
    property = Property.query.get_or_404(property_id)
    
    # Check if user owns the property
    if property.landlord_id != current_user.id:
        flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
        return redirect(url_for('landlord.properties'))
    
    # Get the approved application for this property
    application = RentalApplication.query.filter_by(
        property_id=property_id,
        status='approved'
    ).first()
    
    if not application:
        flash('Bu əmlak üçün təsdiqlənmiş müraciət tapılmadı', 'warning')
        return redirect(url_for('landlord.properties'))
    
    # Get contract info status
    landlord_info = current_user.contract_info[0] if current_user.contract_info else None
    property_info_complete = all([
        property.registry_number,
        property.area,
        property.contract_term
    ])
    
    # Calculate contract progress
    progress_steps = 0
    total_steps = 2  # landlord info and property info
    
    if landlord_info:
        progress_steps += 1
    if property_info_complete:
        progress_steps += 1
        
    contract_progress = int((progress_steps / total_steps) * 100)
    contract_ready = progress_steps == total_steps
    
    return render_template('landlord/property_contract.html',
                         property=property,
                         application=application,
                         landlord_info=landlord_info,
                         property_info_complete=property_info_complete,
                         contract_progress=contract_progress,
                         contract_ready=contract_ready)

@landlord_bp.route('/landlord/api/applications')
@login_required
@landlord_required
def get_applications():
    """Get all applications for properties owned by the landlord"""
    try:
        # Get all properties owned by the landlord
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
        property_ids = [p.id for p in properties]
        
        # Get all applications for these properties
        applications = RentalApplication.query.filter(
            RentalApplication.property_id.in_(property_ids)
        ).all()
        
        # Format applications data
        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'property': {
                    'id': app.rental_property.id,
                    'title': app.rental_property.title,
                    'address': app.rental_property.address
                },
                'tenant': {
                    'id': app.tenant.id,
                    'name': app.tenant.name
                },
                'status': app.status,
                'contract_status': app.contract_status or 'draft',
                'created_at': app.created_at.isoformat()
            })
        
        return jsonify(applications_data)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching applications: {str(e)}")
        return jsonify({'error': 'Failed to fetch applications'}), 500

@landlord_bp.route('/landlord/api/applications/<application_id>', methods=['PUT'])
@login_required
@landlord_required
def update_application_status(application_id):
    """Update application status"""
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in ['approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
            
        application = RentalApplication.query.get_or_404(application_id)
        
        # Verify landlord owns the property
        if application.rental_property.landlord_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        application.status = status
        
        # Update property status when application is approved
        if status == 'approved':
            application.rental_property.status = 'pending_contract'
            # Reject all other pending applications for this property
            RentalApplication.query.filter_by(
                property_id=application.property_id,
                status='pending'
            ).filter(
                RentalApplication.id != application_id
            ).update({'status': 'rejected'})
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@landlord_bp.route('/landlord/api/contracts')
@login_required
@landlord_required
def get_contracts():
    """Get all contracts for the landlord"""
    # First get all property IDs owned by the landlord
    property_ids = [p.id for p in Property.query.filter_by(landlord_id=current_user.id).all()]
    
    # Then get all applications for these properties
    applications = RentalApplication.query.filter(
        RentalApplication.property_id.in_(property_ids)
    ).all()
    
    contracts = []
    for app in applications:
        # Check if landlord info is complete
        landlord_info = UserContractInfo.query.filter_by(user_id=current_user.id).first()
        landlord_info_complete = bool(landlord_info)
        
        # Check if property info is complete
        property = app.rental_property
        property_info_complete = all([
            property.registry_number,
            property.area,
            property.contract_term
        ])
        
        contracts.append({
            'id': app.id,
            'property': {
                'title': property.title,
                'address': property.address
            },
            'status': app.contract_status or 'draft',
            'landlord_info_complete': landlord_info_complete,
            'property_info_complete': property_info_complete,
            'landlord_signature': bool(app.landlord_signature),
            'tenant_signature': bool(app.tenant_signature)
        })
    
    return jsonify(contracts)

@landlord_bp.route('/landlord/api/ratings/received')
@login_required
@landlord_required
def get_received_ratings():
    """Get all ratings received by the landlord"""
    try:
        # Get all ratings received by the landlord, ordered by creation date
        ratings = Rating.query.filter_by(ratee_id=current_user.id)\
            .order_by(Rating.created_at.desc()).all()
        
        # Keep track of unique tenant/property combinations
        seen_combinations = set()
        ratings_data = []
        
        for rating in ratings:
            # Get the application and property for this rating
            application = RentalApplication.query.get(rating.application_id)
            if not application:
                continue
                
            property = application.rental_property
            tenant = User.query.get(rating.rater_id)
            
            # Create a unique key for this tenant/property combination
            combination_key = f"{tenant.id}_{property.id}"
            
            # Only include the rating if we haven't seen this combination before
            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                
                ratings_data.append({
                    'id': rating.id,
                    'contract_id': application.id,
                    'property': {
                        'id': property.id,
                        'title': property.title,
                        'address': property.address
                    },
                    'tenant': {
                        'id': tenant.id,
                        'name': tenant.name
                    },
                    'reliability': rating.reliability,
                    'responsibility': rating.responsibility,
                    'communication': rating.communication,
                    'respect': rating.respect,
                    'compliance': rating.compliance,
                    'review': rating.review,
                    'created_at': rating.created_at.isoformat()
                })
        
        return jsonify(ratings_data)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching ratings: {str(e)}")
        return jsonify({'error': 'Failed to fetch ratings'}), 500

@landlord_bp.route('/landlord/api/ratings/given')
@login_required
@landlord_required
def get_given_ratings():
    """Get all ratings given by the landlord"""
    try:
        # Get all ratings given by the landlord, ordered by creation date
        ratings = Rating.query.filter_by(rater_id=current_user.id)\
            .order_by(Rating.created_at.desc()).all()
        
        # Keep track of unique tenant/property combinations
        seen_combinations = set()
        ratings_data = []
        
        for rating in ratings:
            # Get the application and property for this rating
            application = RentalApplication.query.get(rating.application_id)
            if not application:
                continue
                
            property = application.rental_property
            tenant = User.query.get(rating.ratee_id)
            
            # Create a unique key for this tenant/property combination
            combination_key = f"{tenant.id}_{property.id}"
            
            # Only include the rating if we haven't seen this combination before
            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                
                ratings_data.append({
                    'id': rating.id,
                    'contract_id': application.id,
                    'property': {
                        'id': property.id,
                        'title': property.title,
                        'address': property.address
                    },
                    'tenant': {
                        'id': tenant.id,
                        'name': tenant.name
                    },
                    'reliability': rating.reliability,
                    'responsibility': rating.responsibility,
                    'communication': rating.communication,
                    'respect': rating.respect,
                    'compliance': rating.compliance,
                    'review': rating.review,
                    'created_at': rating.created_at.isoformat()
                })
        
        return jsonify(ratings_data)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching ratings: {str(e)}")
        return jsonify({'error': 'Failed to fetch ratings'}), 500 