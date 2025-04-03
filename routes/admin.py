from flask import Blueprint, render_template, jsonify, abort
from flask_login import login_required, current_user
from models import db, User, Property, Rating, TenantScore, TenantQuestionnaire
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/api/admin/users')
@login_required
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat(),
        'ratings_received': len(user.ratings_received),
        'ratings_given': len(user.ratings_given),
        'tenant_score': user.tenant_score.total_score if user.tenant_score else None,
        'properties_count': len(user.properties) if hasattr(user, 'properties') else 0,
        'avg_rating': sum(r.rating for r in user.ratings_received) / len(user.ratings_received) 
            if user.ratings_received else 0
    } for user in users])

@admin_bp.route('/api/admin/users/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting the admin user
    if user.role == 'admin':
        return jsonify({'error': 'Cannot delete admin user'}), 403
    
    try:
        # Delete associated ratings
        Rating.query.filter(
            (Rating.rater_id == user_id) | (Rating.ratee_id == user_id)
        ).delete()
        
        # Delete tenant score if exists
        if user.role == 'tenant':
            TenantScore.query.filter_by(tenant_id=user_id).delete()
            
        # Delete properties if landlord
        if user.role == 'landlord':
            Property.query.filter_by(landlord_id=user_id).delete()
            
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/ratings')
@login_required
@admin_required
def get_ratings():
    ratings = Rating.query.all()
    return jsonify([{
        'id': rating.id,
        'rater_name': rating.rater.name,
        'ratee_name': rating.ratee.name,
        'property_title': rating.property.title if rating.property else None,
        'created_at': rating.created_at.isoformat(),
        'average_rating': 
            sum(filter(None, [
                rating.reliability,  # Property accuracy/Payment discipline
                rating.responsibility,  # Contract transparency/Property care
                rating.communication,  # Communication
                rating.compliance,  # Maintenance/Contract compliance
                rating.respect  # Privacy respect/Neighbor relations
            ])) / len(list(filter(None, [
                rating.reliability,
                rating.responsibility,
                rating.communication,
                rating.compliance,
                rating.respect
            ]))) if any([
                rating.reliability,
                rating.responsibility,
                rating.communication,
                rating.compliance,
                rating.respect
            ]) else 0,
        'reliability': rating.reliability,
        'responsibility': rating.responsibility,
        'communication': rating.communication,
        'compliance': rating.compliance,
        'respect': rating.respect,
        'review': rating.review
    } for rating in ratings])

@admin_bp.route('/api/admin/ratings/<rating_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)
    
    try:
        db.session.delete(rating)
        db.session.commit()
        return jsonify({'message': 'Rating deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/credit-scores')
@login_required
@admin_required
def get_credit_scores():
    """Get all credit scores with tenant information"""
    scores = TenantQuestionnaire.query.all()
    return jsonify([{
        'id': score.id,
        'tenant_name': score.tenant.name,
        'tenant_email': score.tenant.email,
        'credit_score': score.credit_score,
        'age_group': score.age_group,
        'education': score.education,
        'work_sector': score.work_sector,
        'work_experience': score.work_experience,
        'credit_history': score.credit_history,
        'created_at': score.created_at.isoformat()
    } for score in scores])

@admin_bp.route('/api/admin/credit-scores/<score_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_credit_score(score_id):
    """Delete a credit score"""
    score = TenantQuestionnaire.query.get_or_404(score_id)
    
    try:
        db.session.delete(score)
        db.session.commit()
        return jsonify({'message': 'Credit score deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 