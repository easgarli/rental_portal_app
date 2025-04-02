from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import TenantScore, User
from datetime import datetime

tenant_score_bp = Blueprint('tenant_score', __name__)

@tenant_score_bp.route('/tenant-score/<tenant_id>', methods=['GET'])
@login_required
def get_tenant_score(tenant_id):
    tenant = User.query.get(tenant_id)
    
    if not tenant or tenant.role != 'tenant':
        return jsonify({'error': 'Yanlış icarədar ID'}), 400
        
    score = TenantScore.query.filter_by(tenant_id=tenant_id).first()
    
    if not score:
        return jsonify({
            'total_score': 0,
            'payment_score': 0,
            'property_score': 0,
            'rental_history_score': 0,
            'neighbor_score': 0,
            'contract_score': 0,
            'updated_at': datetime.utcnow().isoformat()
        })
        
    return jsonify({
        'total_score': score.total_score,
        'payment_score': score.payment_score,
        'property_score': score.property_score,
        'rental_history_score': score.rental_history_score,
        'neighbor_score': score.neighbor_score,
        'contract_score': score.contract_score,
        'updated_at': score.updated_at.isoformat()
    }) 