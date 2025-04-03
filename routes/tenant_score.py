from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import TenantScore, User, TenantQuestionnaire, Rating
from datetime import datetime

tenant_score_bp = Blueprint('tenant_score', __name__)

@tenant_score_bp.route('/api/tenant-score/<tenant_id>')
@login_required
def get_credit_score(tenant_id):
    """Get tenant's credit score from questionnaire"""
    tenant = User.query.get(tenant_id)
    
    if not tenant or tenant.role != 'tenant':
        return jsonify({'error': 'Yanlış icarədar ID'}), 400
        
    # Get questionnaire score
    questionnaire = TenantQuestionnaire.query.filter_by(tenant_id=tenant_id).first()
    
    if not questionnaire:
        return jsonify({'error': 'Kredit skorinq anketi doldurulmayıb'}), 404
    
    return jsonify({
        'credit_score': questionnaire.credit_score,
        'updated_at': questionnaire.created_at.isoformat()
    })

@tenant_score_bp.route('/tenant-score/<tenant_id>')
@login_required
def get_tenant_score(tenant_id):
    """Get tenant's score based on ratings"""
    # Print for debugging
    print(f"Fetching score for tenant: {tenant_id}")
    
    # Get all ratings for this tenant
    ratings = Rating.query.filter_by(ratee_id=tenant_id).all()
    
    # Print for debugging
    print(f"Found {len(ratings)} ratings")
    
    if not ratings:
        return jsonify({
            'payment_score': 0,
            'property_score': 0,
            'rental_history_score': 0,
            'neighbor_score': 0,
            'contract_score': 0,
            'total_score': 0,
            'updated_at': datetime.utcnow().isoformat()
        })
    
    # Calculate average scores
    payment_score = sum(r.reliability for r in ratings if r.reliability) / len([r for r in ratings if r.reliability]) * 20
    property_score = sum(r.responsibility for r in ratings if r.responsibility) / len([r for r in ratings if r.responsibility]) * 20
    rental_history_score = sum(r.communication for r in ratings if r.communication) / len([r for r in ratings if r.communication]) * 20
    neighbor_score = sum(r.respect for r in ratings if r.respect) / len([r for r in ratings if r.respect]) * 20
    contract_score = sum(r.compliance for r in ratings if r.compliance) / len([r for r in ratings if r.compliance]) * 20
    
    total_score = (payment_score + property_score + rental_history_score + neighbor_score + contract_score) / 5
    
    # Print for debugging
    print(f"Calculated scores: payment={payment_score}, property={property_score}, rental={rental_history_score}, neighbor={neighbor_score}, contract={contract_score}, total={total_score}")
    
    return jsonify({
        'payment_score': payment_score,
        'property_score': property_score,
        'rental_history_score': rental_history_score,
        'neighbor_score': neighbor_score,
        'contract_score': contract_score,
        'total_score': total_score,
        'updated_at': datetime.utcnow().isoformat()
    }) 