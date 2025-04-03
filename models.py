from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('tenant', 'landlord', 'admin', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    ratings_given = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater')
    ratings_received = db.relationship('Rating', foreign_keys='Rating.ratee_id', backref='ratee')
    tenant_score = db.relationship('TenantScore', backref='tenant', uselist=False)

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rater_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    ratee_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    review = db.Column(db.Text)
    
    # Rating components
    reliability = db.Column(db.Integer, nullable=False)
    responsibility = db.Column(db.Integer, nullable=False)
    communication = db.Column(db.Integer, nullable=False)
    respect = db.Column(db.Integer, nullable=False)
    compliance = db.Column(db.Integer, nullable=False)
    
    property = db.relationship('Property', backref='ratings')

class TenantScore(db.Model):
    __tablename__ = 'tenant_scores'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Component scores
    payment_score = db.Column(db.Float, default=0)
    property_score = db.Column(db.Float, default=0)
    rental_history_score = db.Column(db.Float, default=0)
    neighbor_score = db.Column(db.Float, default=0)
    contract_score = db.Column(db.Float, default=0)
    total_score = db.Column(db.Float, default=0)
    
    payment_history = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_total_score(self):
        """Calculate weighted total score"""
        weights = {
            'payment': 0.30,
            'property': 0.25,
            'history': 0.20,
            'neighbor': 0.15,
            'contract': 0.10
        }
        
        self.total_score = (
            self.payment_score * weights['payment'] +
            self.property_score * weights['property'] +
            self.rental_history_score * weights['history'] +
            self.neighbor_score * weights['neighbor'] +
            self.contract_score * weights['contract']
        )
        
        return self.total_score

    @staticmethod
    def calculate_component_scores(ratings):
        """Calculate component scores from ratings"""
        if not ratings:
            return {
                'payment_score': 0,
                'property_score': 0,
                'rental_history_score': 0,
                'neighbor_score': 0,
                'contract_score': 0
            }
        
        scores = {
            'payment_score': sum(r.reliability or 0 for r in ratings) / len(ratings) * 20,
            'property_score': sum(r.responsibility or 0 for r in ratings) / len(ratings) * 20,
            'neighbor_score': sum(r.respect or 0 for r in ratings) / len(ratings) * 20,
            'contract_score': sum(r.compliance or 0 for r in ratings) / len(ratings) * 20
        }
        
        # Calculate rental history score based on length and consistency
        history_length = (max(r.created_at for r in ratings) - min(r.created_at for r in ratings)).days / 365.0
        history_score = min(history_length * 10, 100)  # Cap at 100
        scores['rental_history_score'] = history_score
        
        return scores 

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    monthly_rent = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    available_from = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.Enum('available', 'rented', 'unavailable', name='property_status'), default='available')
    
    # Relationships
    landlord = db.relationship('User', backref='properties')
    
    def to_dict(self):
        """Convert property to dictionary with landlord rating"""
        from sqlalchemy import func
        
        # Calculate landlord's average rating for this specific property
        avg_rating = db.session.query(
            func.avg(
                (Rating.reliability + Rating.responsibility + 
                 Rating.communication + Rating.respect + Rating.compliance) / 5.0
            ))\
            .filter(
                Rating.ratee_id == self.landlord_id,
                Rating.property_id == self.id
            ).scalar() or 0
            
        # Get total ratings count for this property
        ratings_count = Rating.query.filter(
            Rating.ratee_id == self.landlord_id,
            Rating.property_id == self.id
        ).count()
            
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'monthly_rent': self.monthly_rent,
            'address': self.address,
            'available_from': self.available_from.isoformat(),
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'landlord': {
                'id': self.landlord.id,
                'name': self.landlord.name,
                'avg_rating': round(float(avg_rating), 1),
                'ratings_count': ratings_count
            }
        } 

class TenantQuestionnaire(db.Model):
    __tablename__ = 'tenant_questionnaires'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    age_group = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    dependents = db.Column(db.String(20), nullable=False)
    education = db.Column(db.String(20), nullable=False)
    work_sector = db.Column(db.String(50), nullable=False)
    work_experience = db.Column(db.String(20), nullable=False)
    credit_history = db.Column(db.String(50), nullable=False)
    monthly_income = db.Column(db.Float, nullable=False)
    monthly_expenses = db.Column(db.Float, nullable=False)
    planned_rent = db.Column(db.Float, nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tenant = db.relationship('User', backref='questionnaire') 