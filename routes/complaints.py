from flask import Blueprint, jsonify, request
from models import db, Complaint, Property, User
from decorators import login_required, role_required
from datetime import datetime, UTC
import uuid

complaints_bp = Blueprint('complaints', __name__)

@complaints_bp.route('/api/complaints', methods=['POST'])
@login_required
@role_required('tenant')
def create_complaint():
    """Create a new complaint"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['property_id', 'severity', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create new complaint
        complaint = Complaint(
            id=str(uuid.uuid4()),
            tenant_id=request.user.id,  # Current user is the tenant
            property_id=data['property_id'],
            severity=data['severity'],
            description=data['description'],
            status='open'
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint created successfully',
            'complaint': complaint.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@complaints_bp.route('/api/complaints/<complaint_id>', methods=['GET'])
@login_required
def get_complaint(complaint_id):
    """Get complaint details"""
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
        
    return jsonify(complaint.to_dict())

@complaints_bp.route('/api/complaints/property/<property_id>', methods=['GET'])
@login_required
def get_property_complaints(property_id):
    """Get all complaints for a property"""
    complaints = Complaint.query.filter_by(property_id=property_id).all()
    return jsonify([complaint.to_dict() for complaint in complaints])

@complaints_bp.route('/api/complaints/<complaint_id>/status', methods=['PUT'])
@login_required
@role_required('landlord')
def update_complaint_status(complaint_id):
    """Update complaint status"""
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
        
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
        
    try:
        complaint.status = data['status']
        complaint.updated_at = datetime.now(UTC)
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint status updated successfully',
            'complaint': complaint.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@complaints_bp.route('/api/complaints/tenant/<tenant_id>', methods=['GET'])
@login_required
def get_tenant_complaints(tenant_id):
    """Get all complaints by a tenant"""
    complaints = Complaint.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([complaint.to_dict() for complaint in complaints])

@complaints_bp.route('/api/complaints/landlord/<landlord_id>', methods=['GET'])
@login_required
@role_required('landlord')
def get_landlord_complaints(landlord_id):
    """Get all complaints for properties owned by a landlord"""
    complaints = Complaint.query.join(Property).filter(
        Property.landlord_id == landlord_id
    ).all()
    return jsonify([complaint.to_dict() for complaint in complaints])

@complaints_bp.route('/api/complaints/<complaint_id>/resolve', methods=['POST'])
@login_required
@role_required('landlord')
def resolve_complaint(complaint_id):
    """Resolve a complaint"""
    data = request.get_json()
    if 'resolution' not in data:
        return jsonify({'error': 'Resolution details are required'}), 400
        
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
        
    try:
        complaint.status = 'resolved'
        complaint.resolution = data['resolution']
        complaint.updated_at = datetime.now(UTC)
        db.session.commit()
        
        return jsonify({
            'message': 'Complaint resolved successfully',
            'complaint': complaint.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 