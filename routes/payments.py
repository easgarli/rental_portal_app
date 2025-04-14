from flask import Blueprint, jsonify, request
from models import db, Payment, Contract, User
from decorators import login_required, role_required
from datetime import datetime, UTC
import uuid

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/api/payments', methods=['POST'])
@login_required
@role_required('tenant')
def create_payment():
    """Create a new payment"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['contract_id', 'amount', 'due_date', 'payment_method']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Create new payment
        payment = Payment(
            id=str(uuid.uuid4()),
            contract_id=data['contract_id'],
            amount=data['amount'],
            due_date=datetime.fromisoformat(data['due_date']),
            payment_method=data['payment_method'],
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment created successfully',
            'payment': payment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/api/payments/<payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id):
    """Get payment details"""
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
        
    return jsonify(payment.to_dict())

@payments_bp.route('/api/payments/contract/<contract_id>', methods=['GET'])
@login_required
def get_contract_payments(contract_id):
    """Get all payments for a contract"""
    payments = Payment.query.filter_by(contract_id=contract_id).all()
    return jsonify([payment.to_dict() for payment in payments])

@payments_bp.route('/api/payments/<payment_id>/status', methods=['PUT'])
@login_required
@role_required('landlord')
def update_payment_status(payment_id):
    """Update payment status"""
    data = request.get_json()
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
        
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
        
    try:
        payment.status = data['status']
        payment.updated_at = datetime.now(UTC)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment status updated successfully',
            'payment': payment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/api/payments/user/<user_id>', methods=['GET'])
@login_required
def get_user_payments(user_id):
    """Get all payments for a user"""
    payments = Payment.query.join(Contract).filter(
        (Contract.tenant_id == user_id) | (Contract.landlord_id == user_id)
    ).all()
    return jsonify([payment.to_dict() for payment in payments])

@payments_bp.route('/api/payments/<payment_id>/refund', methods=['POST'])
@login_required
@role_required('landlord')
def request_refund(payment_id):
    """Request a refund for a payment"""
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
        
    if payment.status != 'completed':
        return jsonify({'error': 'Only completed payments can be refunded'}), 400
        
    try:
        payment.status = 'refunded'
        payment.updated_at = datetime.now(UTC)
        db.session.commit()
        
        return jsonify({
            'message': 'Refund requested successfully',
            'payment': payment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 