from flask import Blueprint, render_template, jsonify, abort, current_app
from flask_login import login_required, current_user
from models import db, User, Property, Rating, TenantScore, TenantQuestionnaire, RentalApplication
from functools import wraps
from utils.database import DatabaseManager, DatabaseConfig
import os

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
        'avg_rating': calculate_avg_rating(user.ratings_received) if user.ratings_received else 0
    } for user in users])

def calculate_avg_rating(ratings):
    """Calculate average rating from all rating dimensions"""
    if not ratings:
        return 0
        
    total_sum = 0
    total_count = 0
    
    for rating in ratings:
        dimensions = [
            rating.reliability,
            rating.responsibility,
            rating.communication,
            rating.compliance,
            rating.respect
        ]
        # Filter out None values
        valid_dimensions = [r for r in dimensions if r is not None]
        if valid_dimensions:
            total_sum += sum(valid_dimensions)
            total_count += len(valid_dimensions)
    
    return round(total_sum / total_count, 2) if total_count > 0 else 0

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

@admin_bp.route('/api/admin/databases')
@login_required
@admin_required
def get_databases():
    """Get list of all databases"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text("""
                SELECT datname FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname;
            """))
            databases = [row[0] for row in result]
            return jsonify(databases)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/tables/<database>')
@login_required
@admin_required
def get_tables(database):
    """Get all tables in a database"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [{'name': row[0], 'type': row[1]} for row in result]
            return jsonify(tables)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/admin/columns/<table>')
@login_required
@admin_required
def get_columns(table):
    """Get column information for a table"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """), {'table': table})
            columns = [{
                'name': row[0],
                'type': row[1],
                'nullable': row[2],
                'default': row[3]
            } for row in result]
            return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/contracts')
@login_required
@admin_required
def get_contracts():
    try:
        # Get all rental applications with contracts and eager load relationships
        applications = RentalApplication.query.options(
            db.joinedload(RentalApplication.tenant),
            db.joinedload(RentalApplication.rental_property).joinedload(Property.landlord)
        ).filter(
            RentalApplication.contract_status != 'draft'
        ).all()
        
        contracts_data = []
        for app in applications:
            try:
                # Safely access nested relationships
                property_title = app.rental_property.title if app.rental_property else 'Unknown'
                property_address = app.rental_property.address if app.rental_property else 'Unknown'
                
                tenant_name = app.tenant.name if app.tenant else 'Unknown'
                tenant_id = app.tenant.id if app.tenant else None
                
                landlord_name = app.rental_property.landlord.name if app.rental_property and app.rental_property.landlord else 'Unknown'
                landlord_id = app.rental_property.landlord.id if app.rental_property and app.rental_property.landlord else None
                
                contract_data = {
                    'id': app.id,
                    'application_id': app.id,
                    'property': {
                        'title': property_title,
                        'address': property_address
                    },
                    'tenant': {
                        'id': tenant_id,
                        'name': tenant_name
                    },
                    'landlord': {
                        'id': landlord_id,
                        'name': landlord_name
                    },
                    'monthly_rent': float(app.rental_property.monthly_rent) if app.rental_property and app.rental_property.monthly_rent else None,
                    'currency': app.rental_property.currency if app.rental_property else 'AZN',
                    'status': app.contract_status or 'draft',
                    'created_at': app.created_at.strftime('%Y-%m-%dT%H:%M:%S') if app.created_at else None,
                    'tenant_signature': app.tenant_signature is not None,
                    'landlord_signature': app.landlord_signature is not None
                }
                contracts_data.append(contract_data)
            except Exception as e:
                current_app.logger.error(f"Error processing contract {app.id}: {str(e)}")
                continue
        
        if not contracts_data:
            return jsonify([])
            
        return jsonify(contracts_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching contracts: {str(e)}")
        return jsonify({
            'error': 'Müqavilələr yüklənərkən xəta baş verdi'
        }), 500

@admin_bp.route('/admin/contracts/<application_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_contract(application_id):
    """Delete a contract"""
    try:
        application = RentalApplication.query.get_or_404(application_id)
        
        # Reset contract-related fields
        application.contract_status = 'draft'
        application.contract_content = None
        application.contract_generated_at = None
        application.tenant_signature = None
        application.landlord_signature = None
        
        # Reset property status if it was rented
        if application.rental_property.status == 'rented':
            application.rental_property.status = 'available'
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Müqavilə uğurla silindi'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting contract: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 