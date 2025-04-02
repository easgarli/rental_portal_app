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
    role = db.Column(db.Enum('tenant', 'landlord', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ratings_given = db.relationship('Rating', backref='rater', foreign_keys='Rating.rater_id')
    ratings_received = db.relationship('Rating', backref='ratee', foreign_keys='Rating.ratee_id')
    tenant_score = db.relationship('TenantScore', backref='tenant', uselist=False)

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rater_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    ratee_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    review = db.Column(db.Text)
    
    # Tenant rating fields
    payment_discipline = db.Column(db.Integer)
    property_care = db.Column(db.Integer)
    communication = db.Column(db.Integer)
    neighbor_relations = db.Column(db.Integer)
    contract_compliance = db.Column(db.Integer)
    
    # Landlord rating fields
    property_accuracy = db.Column(db.Integer)
    contract_transparency = db.Column(db.Integer)
    support_communication = db.Column(db.Integer)
    maintenance = db.Column(db.Integer)
    privacy_respect = db.Column(db.Integer)

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
            'payment_score': sum(r.payment_discipline or 0 for r in ratings) / len(ratings) * 20,
            'property_score': sum(r.property_care or 0 for r in ratings) / len(ratings) * 20,
            'neighbor_score': sum(r.neighbor_relations or 0 for r in ratings) / len(ratings) * 20,
            'contract_score': sum(r.contract_compliance or 0 for r in ratings) / len(ratings) * 20
        }
        
        # Calculate rental history score based on length and consistency
        history_length = (max(r.created_at for r in ratings) - min(r.created_at for r in ratings)).days / 365.0
        history_score = min(history_length * 10, 100)  # Cap at 100
        scores['rental_history_score'] = history_score
        
        return scores 