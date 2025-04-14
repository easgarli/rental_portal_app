from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Rating, User, TenantScore, RentalApplication, Payment, PropertyDamage, Complaint, ContractViolation
from datetime import datetime, UTC, timedelta
from flask_wtf.csrf import CSRFProtect
from utils.csrf import csrf
from functools import wraps

ratings_bp = Blueprint('ratings', __name__)

# Add this decorator to exempt routes from CSRF protection
def csrf_exempt(view):
    if isinstance(view, str):
        view_location = view
    else:
        view_location = '.'.join((view.__module__, view.__name__))
    csrf._exempt_views.add(view_location)
    return view

def update_tenant_score(tenant_id):
    """Update tenant's score based on all ratings"""
    tenant = User.query.get(tenant_id)
    if not tenant or tenant.role != 'tenant':
        return
    
    ratings = Rating.query.filter_by(ratee_id=tenant_id).all()
    
    # Get or create tenant score
    tenant_score = TenantScore.query.filter_by(tenant_id=tenant_id).first()
    if not tenant_score:
        tenant_score = TenantScore(tenant_id=tenant_id)
        db.session.add(tenant_score)
    
    # Calculate component scores
    scores = TenantScore.calculate_component_scores(ratings)
    
    # Update scores
    for key, value in scores.items():
        setattr(tenant_score, key, value)
    
    # Calculate total score
    tenant_score.calculate_total_score()
    
    db.session.commit()

def tenant_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'tenant':
            flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def landlord_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'landlord':
            flash('Bu əməliyyat üçün icazəniz yoxdur', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@ratings_bp.route('/rate/landlord/<landlord_id>/contract/<contract_id>', methods=['GET', 'POST'])
@login_required
@tenant_required
def rate_landlord(landlord_id, contract_id):
    """Rate a landlord"""
    landlord = User.query.get_or_404(landlord_id)
    application = RentalApplication.query.get_or_404(contract_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Check if a rating already exists for this property
            existing_rating = Rating.query.filter_by(
                rater_id=current_user.id,
                ratee_id=landlord_id,
                property_id=application.property_id
            ).first()
            
            if existing_rating:
                # Update existing rating
                existing_rating.reliability = data.get('reliability', 0)
                existing_rating.responsibility = data.get('responsibility', 0)
                existing_rating.communication = data.get('communication', 0)
                existing_rating.respect = data.get('respect', 0)
                existing_rating.compliance = data.get('compliance', 0)
                existing_rating.review = data.get('review', '')
                existing_rating.created_at = datetime.utcnow()
            else:
                # Create new rating
                rating = Rating(
                    rater_id=current_user.id,
                    ratee_id=landlord_id,
                    application_id=contract_id,
                    property_id=application.property_id,
                    reliability=data.get('reliability', 0),
                    responsibility=data.get('responsibility', 0),
                    communication=data.get('communication', 0),
                    respect=data.get('respect', 0),
                    compliance=data.get('compliance', 0),
                    review=data.get('review', '')
                )
                db.session.add(rating)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Qiymətləndirmə uğurla əlavə edildi'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return render_template('ratings/rate_landlord.html', 
                         landlord=landlord,
                         contract_id=contract_id)

@ratings_bp.route('/rate/tenant/<tenant_id>/contract/<contract_id>', methods=['GET', 'POST'])
@login_required
@landlord_required
def rate_tenant(tenant_id, contract_id):
    """Rate a tenant"""
    tenant = User.query.get_or_404(tenant_id)
    application = RentalApplication.query.get_or_404(contract_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Check if a rating already exists for this property
            existing_rating = Rating.query.filter_by(
                rater_id=current_user.id,
                ratee_id=tenant_id,
                property_id=application.property_id
            ).first()
            
            if existing_rating:
                # Update existing rating
                existing_rating.reliability = data.get('reliability', 0)
                existing_rating.responsibility = data.get('responsibility', 0)
                existing_rating.communication = data.get('communication', 0)
                existing_rating.respect = data.get('respect', 0)
                existing_rating.compliance = data.get('compliance', 0)
                existing_rating.review = data.get('review', '')
                existing_rating.created_at = datetime.utcnow()
            else:
                # Create new rating
                rating = Rating(
                    rater_id=current_user.id,
                    ratee_id=tenant_id,
                    application_id=contract_id,
                    property_id=application.property_id,
                    reliability=data.get('reliability', 0),
                    responsibility=data.get('responsibility', 0),
                    communication=data.get('communication', 0),
                    respect=data.get('respect', 0),
                    compliance=data.get('compliance', 0),
                    review=data.get('review', '')
                )
                db.session.add(rating)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Qiymətləndirmə uğurla əlavə edildi'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return render_template('ratings/rate_tenant.html', 
                         tenant=tenant,
                         contract_id=contract_id)

@ratings_bp.route('/ratings/<user_id>', methods=['GET'])
@login_required
def get_user_ratings(user_id):
    """Get all ratings for a user"""
    ratings = Rating.query.filter_by(ratee_id=user_id).all()
    
    return jsonify([{
        'id': r.id,
        # Calculate average rating from components
        'rating': round((r.reliability + r.responsibility + r.communication + 
                        r.respect + r.compliance) / 5, 1),
        'reliability': r.reliability,
        'responsibility': r.responsibility,
        'communication': r.communication,
        'respect': r.respect,
        'compliance': r.compliance,
        'review': r.review,
        'rater': {
            'name': r.rater.name,
            'email': r.rater.email,
            'role': r.rater.role
        },
        'created_at': r.created_at.isoformat(),
        'property': {
            'title': r.property.title,
            'address': r.property.address
        } if r.property else None
    } for r in ratings])

@ratings_bp.route('/ratings/received/<user_id>', methods=['GET'])
@login_required
def get_received_ratings(user_id):
    """Get all ratings received by a user"""
    ratings = Rating.query.filter_by(ratee_id=user_id).all()
    
    return jsonify([{
        'id': r.id,
        'reliability': r.reliability,
        'responsibility': r.responsibility,
        'communication': r.communication,
        'respect': r.respect,
        'compliance': r.compliance,
        'review': r.review,
        'created_at': r.created_at.isoformat(),
        'rater': {
            'id': r.rater.id,
            'name': r.rater.name
        },
        'property': {
            'id': r.property.id,
            'title': r.property.title
        } if r.property else None
    } for r in ratings])

@ratings_bp.route('/ratings/given/<user_id>')
@login_required
def get_given_ratings(user_id):
    """Get ratings given by a specific user"""
    if current_user.id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    ratings = Rating.query.filter_by(rater_id=user_id).all()
    
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

@ratings_bp.route('/api/tenant-score/<tenant_id>', methods=['GET'])
@login_required
def get_tenant_score(tenant_id):
    """Get tenant's current score and history"""
    tenant_score = TenantScore.query.filter_by(tenant_id=tenant_id).first()
    if not tenant_score:
        return jsonify({'error': 'Tenant score not found'}), 404
        
    return jsonify({
        'total_score': tenant_score.total_score,
        'component_scores': {
            'payment': tenant_score.payment_score,
            'property': tenant_score.property_score,
            'rental_history': tenant_score.rental_history_score,
            'neighbor': tenant_score.neighbor_score,
            'contract': tenant_score.contract_score
        },
        'payment_history': tenant_score.payment_history,
        'property_history': tenant_score.property_history,
        'rental_history': tenant_score.rental_history,
        'neighbor_history': tenant_score.neighbor_history,
        'contract_history': tenant_score.contract_history,
        'last_updated': tenant_score.updated_at.isoformat()
    })

@ratings_bp.route('/api/tenant-score/<tenant_id>/history', methods=['GET'])
@login_required
def get_tenant_score_history(tenant_id):
    """Get tenant's score history over time"""
    # Get score changes in the last year
    start_date = datetime.utcnow() - timedelta(days=365)
    payments = Payment.query.filter(
        Payment.tenant_id == tenant_id,
        Payment.created_at >= start_date
    ).order_by(Payment.created_at).all()
    
    damages = PropertyDamage.query.filter(
        PropertyDamage.tenant_id == tenant_id,
        PropertyDamage.created_at >= start_date
    ).order_by(PropertyDamage.created_at).all()
    
    complaints = Complaint.query.filter(
        Complaint.tenant_id == tenant_id,
        Complaint.created_at >= start_date
    ).order_by(Complaint.created_at).all()
    
    violations = ContractViolation.query.filter(
        ContractViolation.tenant_id == tenant_id,
        ContractViolation.created_at >= start_date
    ).order_by(ContractViolation.created_at).all()
    
    return jsonify({
        'payment_history': [p.to_dict() for p in payments],
        'property_history': [d.to_dict() for d in damages],
        'complaint_history': [c.to_dict() for c in complaints],
        'violation_history': [v.to_dict() for v in violations]
    })

@ratings_bp.route('/api/tenant-score/<tenant_id>/predict', methods=['GET'])
@login_required
def predict_tenant_score(tenant_id):
    """Predict tenant's future score based on current trends"""
    tenant_score = TenantScore.query.filter_by(tenant_id=tenant_id).first()
    if not tenant_score:
        return jsonify({'error': 'Tenant score not found'}), 404
        
    # Analyze trends in each component
    trends = {
        'payment': analyze_payment_trend(tenant_id),
        'property': analyze_property_trend(tenant_id),
        'rental': analyze_rental_trend(tenant_id),
        'neighbor': analyze_neighbor_trend(tenant_id),
        'contract': analyze_contract_trend(tenant_id)
    }
    
    # Calculate predicted scores
    predicted_scores = {
        'payment': predict_component_score(tenant_score.payment_score, trends['payment']),
        'property': predict_component_score(tenant_score.property_score, trends['property']),
        'rental': predict_component_score(tenant_score.rental_history_score, trends['rental']),
        'neighbor': predict_component_score(tenant_score.neighbor_score, trends['neighbor']),
        'contract': predict_component_score(tenant_score.contract_score, trends['contract'])
    }
    
    # Calculate predicted total score
    weights = {
        'payment': 0.30,
        'property': 0.25,
        'rental': 0.20,
        'neighbor': 0.15,
        'contract': 0.10
    }
    
    predicted_total = sum(
        score * weights[component]
        for component, score in predicted_scores.items()
    )
    
    return jsonify({
        'current_score': tenant_score.total_score,
        'predicted_score': predicted_total,
        'component_predictions': predicted_scores,
        'trends': trends
    }) 