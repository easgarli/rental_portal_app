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
@csrf_exempt
def rate_tenant():
    if current_user.role != 'landlord':
        return jsonify({'error': 'Yalnız mülk sahibləri icarədarları qiymətləndirə bilər'}), 403
        
    data = request.get_json()
    tenant = User.query.get(data['tenant_id'])
    
    if not tenant or tenant.role != 'tenant':
        return jsonify({'error': 'Yanlış icarədar ID'}), 400
        
    # Calculate overall rating as average of components
    overall_rating = sum([
        data.get('payment_discipline', 0),
        data.get('property_care', 0),
        data.get('communication', 0),
        data.get('neighbor_relations', 0),
        data.get('contract_compliance', 0)
    ]) / 5
    
    rating = Rating(
        rater_id=current_user.id,
        ratee_id=tenant.id,
        rating=round(overall_rating),
        payment_discipline=data.get('payment_discipline'),
        property_care=data.get('property_care'),
        communication=data.get('communication'),
        neighbor_relations=data.get('neighbor_relations'),
        contract_compliance=data.get('contract_compliance'),
        review=data.get('review', '')
    )
    
    db.session.add(rating)
    db.session.commit()
    
    # Update tenant score
    update_tenant_score(tenant.id)
    
    return jsonify({'message': 'Qiymətləndirmə uğurla əlavə edildi'})

@ratings_bp.route('/rate-landlord', methods=['POST'])
@login_required
@csrf_exempt
def rate_landlord():
    try:
        if current_user.role != 'tenant':
            return jsonify({'error': 'Yalnız icarədarlar mülk sahiblərini qiymətləndirə bilər'}), 403
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Məlumatlar düzgün formatda deyil'}), 400
            
        landlord = User.query.get(data['landlord_id'])
        
        if not landlord or landlord.role != 'landlord':
            return jsonify({'error': 'Yanlış mülk sahibi ID'}), 400
            
        # Calculate overall rating as average of components
        overall_rating = sum([
            data.get('property_accuracy', 0),
            data.get('contract_transparency', 0),
            data.get('support_communication', 0),
            data.get('maintenance', 0),
            data.get('privacy_respect', 0)
        ]) / 5
        
        # Check if user has already rated this landlord
        existing_rating = Rating.query.filter_by(
            rater_id=current_user.id,
            ratee_id=landlord.id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = round(overall_rating)
            existing_rating.property_accuracy = data.get('property_accuracy')
            existing_rating.contract_transparency = data.get('contract_transparency')
            existing_rating.support_communication = data.get('support_communication')
            existing_rating.maintenance = data.get('maintenance')
            existing_rating.privacy_respect = data.get('privacy_respect')
            existing_rating.review = data.get('review', '')
        else:
            # Create new rating
            rating = Rating(
                rater_id=current_user.id,
                ratee_id=landlord.id,
                rating=round(overall_rating),
                property_accuracy=data.get('property_accuracy'),
                contract_transparency=data.get('contract_transparency'),
                support_communication=data.get('support_communication'),
                maintenance=data.get('maintenance'),
                privacy_respect=data.get('privacy_respect'),
                review=data.get('review', '')
            )
            db.session.add(rating)
        
        db.session.commit()
        return jsonify({'message': 'Qiymətləndirmə uğurla əlavə edildi'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in rate_landlord: {str(e)}")  # For debugging
        return jsonify({'error': 'Qiymətləndirmə zamanı xəta baş verdi'}), 500

@ratings_bp.route('/ratings/<user_id>', methods=['GET'])
@login_required
def get_user_ratings(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'İstifadəçi tapılmadı'}), 404
        
    ratings = Rating.query.filter_by(ratee_id=user_id).all()
    ratings_data = [{
        'rating': r.rating,
        'review': r.review,
        'rater_name': r.rater.name,
        'created_at': r.created_at.isoformat(),
        'payment_discipline': r.payment_discipline,
        'property_care': r.property_care,
        'communication': r.communication,
        'neighbor_relations': r.neighbor_relations,
        'contract_compliance': r.contract_compliance,
        'property_accuracy': r.property_accuracy,
        'contract_transparency': r.contract_transparency,
        'support_communication': r.support_communication,
        'maintenance': r.maintenance,
        'privacy_respect': r.privacy_respect
    } for r in ratings]
    
    return jsonify(ratings_data) 