from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from models import db, Property, RentalApplication, Rating, TenantScore, User
from functools import wraps

tenant_bp = Blueprint('tenant', __name__)

def tenant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'tenant':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@tenant_bp.route('/tenant/dashboard')
@login_required
@tenant_required
def dashboard():
    return render_template('tenant/dashboard.html')

@tenant_bp.route('/tenant/api/dashboard-data')
@login_required
@tenant_required
def dashboard_data():
    tenant_score = TenantScore.query.filter_by(tenant_id=current_user.id).first()
    latest_questionnaire = current_user.questionnaire[0] if current_user.questionnaire else None
    
    return jsonify({
        'tenant_score': tenant_score.score if tenant_score else None,
        'credit_score': latest_questionnaire.credit_score if latest_questionnaire else None
    })

@tenant_bp.route('/tenant/applications')
@login_required
@tenant_required
def applications():
    # List all applications
    applications = RentalApplication.query.filter_by(tenant_id=current_user.id).all()
    return render_template('tenant/applications.html', applications=applications)

@tenant_bp.route('/tenant/contracts')
@login_required
@tenant_required
def contracts():
    # List all contracts
    contracts = RentalApplication.query.filter_by(
        tenant_id=current_user.id,
        status='approved'
    ).all()
    return render_template('tenant/contracts.html', contracts=contracts)

@tenant_bp.route('/tenant/ratings')
@login_required
@tenant_required
def ratings():
    tenant_score = TenantScore.query.filter_by(tenant_id=current_user.id).first()
    latest_questionnaire = current_user.questionnaire[0] if current_user.questionnaire else None
    
    # Get both received and given ratings
    received_ratings = Rating.query.filter_by(ratee_id=current_user.id).all()
    given_ratings = Rating.query.filter_by(rater_id=current_user.id).all()
    
    return render_template('tenant/ratings.html',
                         tenant_score=tenant_score,
                         latest_questionnaire=latest_questionnaire,
                         received_ratings=received_ratings,
                         given_ratings=given_ratings)

@tenant_bp.route('/tenant/profile')
@login_required
@tenant_required
def profile():
    return render_template('tenant/profile.html')

# API endpoints for AJAX calls
@tenant_bp.route('/tenant/api/applications')
@login_required
@tenant_required
def get_applications():
    applications = RentalApplication.query.filter_by(tenant_id=current_user.id).all()
    return jsonify([{
        'id': app.id,
        'property': {
            'title': app.rental_property.title,
            'address': app.rental_property.address
        },
        'status': app.status,
        'contract_status': app.contract_status,
        'created_at': app.created_at.isoformat()
    } for app in applications])

@tenant_bp.route('/tenant/api/ratings/received')
@login_required
@tenant_required
def get_received_ratings():
    """Get ratings received by the tenant"""
    try:
        # Get all ratings received by the tenant
        ratings = Rating.query.filter_by(ratee_id=current_user.id).all()
        
        if not ratings:
            return jsonify([])

        # Group ratings by property and keep only the latest one for each property
        latest_ratings = {}
        for rating in ratings:
            if rating.property_id not in latest_ratings or \
               rating.created_at > latest_ratings[rating.property_id].created_at:
                latest_ratings[rating.property_id] = rating

        ratings_data = []
        for rating in latest_ratings.values():
            rater = User.query.get(rating.rater_id)
            property = Property.query.get(rating.property_id)
            if rater and property:
                ratings_data.append({
                    'id': rating.id,
                    'rater': {
                        'id': rater.id,
                        'name': rater.name
                    },
                    'property': {
                        'id': property.id,
                        'title': property.title
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
        print(f"Error in get_received_ratings: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/tenant/api/ratings/given')
@login_required
@tenant_required
def get_given_ratings():
    """Get ratings given by the tenant"""
    try:
        ratings = Rating.query.filter_by(rater_id=current_user.id).all()
        return jsonify([{
            'id': rating.id,
            'ratee': {
                'id': rating.ratee.id,
                'name': rating.ratee.name
            },
            'property': {
                'id': rating.property.id,
                'title': rating.property.title
            },
            'reliability': rating.reliability,
            'responsibility': rating.responsibility,
            'communication': rating.communication,
            'respect': rating.respect,
            'compliance': rating.compliance,
            'review': rating.review,
            'created_at': rating.created_at.isoformat()
        } for rating in ratings])
    except Exception as e:
        return jsonify({'error': str(e)}), 500 