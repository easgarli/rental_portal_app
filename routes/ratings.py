from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Rating, User, TenantScore
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from utils.csrf import csrf

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

@ratings_bp.route('/rate-tenant', methods=['POST'])
@login_required
def rate_tenant():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Only landlords can rate tenants'}), 403
        
    data = request.get_json()
    
    if not all(k in data for k in ['tenant_id', 'property_id', 'reliability', 'responsibility', 
                                  'communication', 'respect', 'compliance']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    tenant = User.query.get(data['tenant_id'])
    
    if not tenant or tenant.role != 'tenant':
        return jsonify({'error': 'Yanlış icarədar ID'}), 400
        
    try:
        rating = Rating(
            rater_id=current_user.id,
            ratee_id=data['tenant_id'],
            property_id=data['property_id'],
            reliability=data['reliability'],
            responsibility=data['responsibility'],
            communication=data['communication'],
            respect=data['respect'],
            compliance=data['compliance'],
            review=data.get('review', '')
        )
        
        db.session.add(rating)
        db.session.commit()
        
        # Update tenant score
        update_tenant_score(data['tenant_id'])
        
        return jsonify({'message': 'Qiymətləndirmə uğurla əlavə edildi'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ratings_bp.route('/rate-landlord', methods=['POST'])
@login_required
def rate_landlord():
    if current_user.role != 'tenant':
        return jsonify({'error': 'Only tenants can rate landlords'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = [
        'landlord_id', 'property_id', 'reliability', 'responsibility',
        'communication', 'compliance', 'respect'
    ]
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create rating
        rating = Rating(
            rater_id=current_user.id,
            ratee_id=data['landlord_id'],
            property_id=data['property_id'],
            reliability=data['reliability'],  # Property accuracy
            responsibility=data['responsibility'],  # Contract transparency
            communication=data['communication'],
            compliance=data['compliance'],  # Maintenance
            respect=data['respect'],  # Privacy respect
            review=data.get('review', '')
        )
        
        db.session.add(rating)
        db.session.commit()
        
        return jsonify({'message': 'Rating submitted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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