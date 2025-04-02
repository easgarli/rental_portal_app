from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/tenants')
@login_required
def get_tenants():
    """Get list of all tenants"""
    print(f"Current user role: {current_user.role}")  # Debug print
    
    if current_user.role != 'landlord':
        print(f"Unauthorized access attempt by {current_user.email}")  # Debug print
        return jsonify({'error': 'Unauthorized'}), 403
        
    tenants = User.query.filter_by(role='tenant').all()
    tenant_list = [{
        'id': tenant.id,
        'name': tenant.name,
        'email': tenant.email
    } for tenant in tenants]
    
    print(f"Found {len(tenant_list)} tenants")  # Debug print
    return jsonify(tenant_list)

@users_bp.route('/api/landlords')
@login_required
def get_landlords():
    """Get list of all landlords"""
    if current_user.role != 'tenant':
        return jsonify({'error': 'Unauthorized'}), 403
        
    landlords = User.query.filter_by(role='landlord').all()
    return jsonify([{
        'id': landlord.id,
        'name': landlord.name,
        'email': landlord.email
    } for landlord in landlords]) 