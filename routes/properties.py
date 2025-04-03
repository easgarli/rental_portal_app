from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Property
from datetime import datetime

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('/api/properties/my')
@login_required
def get_my_properties():
    """Get properties for the current landlord"""
    if current_user.role != 'landlord':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        properties = Property.query.filter_by(landlord_id=current_user.id).all()
        return jsonify([{
            'id': prop.id,
            'title': prop.title,
            'description': prop.description,
            'monthly_rent': prop.monthly_rent,
            'address': prop.address,
            'available_from': prop.available_from.isoformat(),
            'status': prop.status
        } for prop in properties])
    except Exception as e:
        print(f"Error fetching properties: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/api/properties')
@login_required
def get_properties():
    """Get properties based on user role and parameters"""
    landlord_id = request.args.get('landlord_id')
    
    # Base query
    query = Property.query
    
    # If user is a landlord, only show their properties
    if current_user.role == 'landlord':
        query = query.filter_by(landlord_id=current_user.id)
    # If landlord_id is provided and user is not a landlord (e.g., tenant)
    elif landlord_id:
        query = query.filter_by(landlord_id=landlord_id)
        
        # Only show available or rented properties
        query = query.filter(Property.status.in_(['available', 'rented']))
        
        # Order by status (available first) and then by creation date
        query = query.order_by(
            Property.status.desc(),
            Property.created_at.desc()
        )
    
    try:
        properties = query.all()
        return jsonify([{
            'id': prop.id,
            'title': prop.title,
            'description': prop.description,
            'monthly_rent': prop.monthly_rent,
            'address': prop.address,
            'available_from': prop.available_from.isoformat(),
            'created_at': prop.created_at.isoformat(),
            'status': prop.status
        } for prop in properties])
    except Exception as e:
        print(f"Error fetching properties: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

@properties_bp.route('/api/public/properties')
def get_public_properties():
    """Get all available properties for public view"""
    query = Property.query.filter_by(status='available')
    
    # Apply filters if provided
    search_text = request.args.get('searchText', '').lower()
    min_price = request.args.get('minPrice', type=float)
    max_price = request.args.get('maxPrice', type=float)
    min_rating = request.args.get('minRating', type=float)
    
    if search_text:
        query = query.filter(
            db.or_(
                Property.title.ilike(f'%{search_text}%'),
                Property.address.ilike(f'%{search_text}%')
            )
        )
    
    if min_price:
        query = query.filter(Property.monthly_rent >= min_price)
    
    if max_price:
        query = query.filter(Property.monthly_rent <= max_price)
    
    properties = query.all()
    
    # Convert to dict and filter by landlord rating if needed
    properties_dict = [prop.to_dict() for prop in properties]
    
    if min_rating:
        properties_dict = [
            prop for prop in properties_dict 
            if prop['landlord']['avg_rating'] >= min_rating
        ]
    
    return jsonify(properties_dict)

@properties_bp.route('/api/properties', methods=['POST'])
@login_required
def create_property():
    """Create a new property listing"""
    if current_user.role != 'landlord':
        return jsonify({'error': 'Yalnız mülk sahibləri əmlak əlavə edə bilər'}), 403
    
    data = request.get_json()
    
    try:
        property = Property(
            landlord_id=current_user.id,
            title=data['title'],
            description=data.get('description', ''),
            monthly_rent=float(data['monthly_rent']),
            address=data['address'],
            available_from=datetime.strptime(data['available_from'], '%Y-%m-%d').date(),
            status='available'
        )
        
        db.session.add(property)
        db.session.commit()
        
        return jsonify(property.to_dict()), 201
        
    except (KeyError, ValueError) as e:
        return jsonify({'error': 'Yanlış məlumat formatı'}), 400

@properties_bp.route('/api/properties/<property_id>', methods=['PUT'])
@login_required
def update_property(property_id):
    """Update a property listing"""
    property = Property.query.get_or_404(property_id)
    
    if property.landlord_id != current_user.id:
        return jsonify({'error': 'İcazə yoxdur'}), 403
    
    data = request.get_json()
    
    try:
        if 'title' in data:
            property.title = data['title']
        if 'description' in data:
            property.description = data['description']
        if 'monthly_rent' in data:
            property.monthly_rent = float(data['monthly_rent'])
        if 'address' in data:
            property.address = data['address']
        if 'available_from' in data:
            property.available_from = datetime.strptime(data['available_from'], '%Y-%m-%d').date()
        if 'status' in data:
            property.status = data['status']
            
        db.session.commit()
        return jsonify(property.to_dict())
        
    except (KeyError, ValueError) as e:
        return jsonify({'error': 'Yanlış məlumat formatı'}), 400

@properties_bp.route('/api/properties/<property_id>', methods=['DELETE'])
@login_required
def delete_property(property_id):
    """Delete a property listing"""
    property = Property.query.get_or_404(property_id)
    
    if property.landlord_id != current_user.id:
        return jsonify({'error': 'İcazə yoxdur'}), 403
        
    db.session.delete(property)
    db.session.commit()
    
    return '', 204 