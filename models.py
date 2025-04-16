from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, UTC
import uuid
from sqlalchemy.dialects.postgresql import UUID, NUMERIC, JSONB, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy import func, event
from sqlalchemy.schema import DDL

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define enums
user_roles = ENUM('tenant', 'landlord', 'admin', name='user_roles')
property_status = ENUM('available', 'pending_contract', 'rented', 'unavailable', name='property_status')
application_status = ENUM(
    'draft', 'pending', 'under_review', 'approved', 'rejected', 'expired',
    name='application_status'
)
contract_status = ENUM('draft', 'pending_signatures', 'active', 'completed', 'terminated', name='contract_status')
payment_status = ENUM('pending', 'processing', 'completed', 'failed', 'refunded', name='payment_status')
complaint_severity = ENUM('minor', 'moderate', 'serious', 'eviction', name='complaint_severity')
complaint_status = ENUM('open', 'resolved', 'closed', name='complaint_status')
damage_severity = ENUM('minor', 'moderate', 'major', 'severe', name='damage_severity')
damage_status = ENUM('reported', 'assessed', 'repaired', 'closed', name='damage_status')
violation_severity = ENUM('minor', 'moderate', 'major', 'termination', name='violation_severity')
violation_status = ENUM('reported', 'investigating', 'resolved', 'closed', name='violation_status')

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    landlord_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200), nullable=False)
    monthly_rent = db.Column(NUMERIC(10, 2), nullable=False)
    available_from = db.Column(db.Date, nullable=False)
    status = db.Column(property_status, nullable=False, default='available')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Property details
    registry_number = db.Column(db.String(100))
    area = db.Column(NUMERIC(10, 2))
    contract_term = db.Column(db.Integer)
    currency = db.Column(db.String(3), default='AZN')

    # Relationships
    landlord = db.relationship('User', foreign_keys=[landlord_id])
    applications = db.relationship('RentalApplication', back_populates='rental_property', cascade='all, delete-orphan')
    contracts = db.relationship('Contract', back_populates='property', cascade='all, delete-orphan')
    damages = db.relationship('PropertyDamage', back_populates='property', cascade='all, delete-orphan')
    ratings = db.relationship('Rating', back_populates='property', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert property to dictionary with landlord rating"""
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
            'monthly_rent': float(self.monthly_rent) if self.monthly_rent else 0,
            'address': self.address,
            'available_from': self.available_from.isoformat(),
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'landlord': {
                'id': self.landlord.id,
                'name': self.landlord.name,
                'avg_rating': round(float(avg_rating), 1),
                'ratings_count': ratings_count
            },
            'registry_number': self.registry_number,
            'area': self.area,
            'contract_term': self.contract_term,
            'currency': self.currency
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(user_roles, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    
    # Relationships
    contract_info = db.relationship('UserContractInfo', back_populates='user', cascade='all, delete-orphan')
    questionnaire = db.relationship('TenantQuestionnaire', back_populates='tenant', cascade='all, delete-orphan')
    tenant_score = db.relationship('TenantScore', back_populates='tenant', cascade='all, delete-orphan')
    ratings_given = db.relationship('Rating', foreign_keys='Rating.rater_id', back_populates='rater', cascade='all, delete-orphan')
    ratings_received = db.relationship('Rating', foreign_keys='Rating.ratee_id', back_populates='ratee', cascade='all, delete-orphan')
    owned_properties = db.relationship('Property', back_populates='landlord', cascade='all, delete-orphan')
    applications = db.relationship('RentalApplication', back_populates='tenant', cascade='all, delete-orphan')
    contracts = db.relationship('Contract', back_populates='tenant', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='tenant', cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', back_populates='tenant', cascade='all, delete-orphan')
    damages = db.relationship('PropertyDamage', back_populates='tenant', cascade='all, delete-orphan')
    violations = db.relationship('ContractViolation', back_populates='tenant', cascade='all, delete-orphan')

class Rating(db.Model):
    __tablename__ = 'ratings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rater_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ratee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    application_id = db.Column(UUID(as_uuid=True), db.ForeignKey('rental_applications.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    review = db.Column(db.Text)
    
    # Rating components
    reliability = db.Column(db.Integer, nullable=False)
    responsibility = db.Column(db.Integer, nullable=False)
    communication = db.Column(db.Integer, nullable=False)
    respect = db.Column(db.Integer, nullable=False)
    compliance = db.Column(db.Integer, nullable=False)
    
    # Relationships
    rater = db.relationship('User', foreign_keys=[rater_id], back_populates='ratings_given')
    ratee = db.relationship('User', foreign_keys=[ratee_id], back_populates='ratings_received')
    property = db.relationship('Property', back_populates='ratings')
    application = db.relationship('RentalApplication', back_populates='ratings')

class TenantScore(db.Model):
    __tablename__ = 'tenant_scores'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Component scores (0-5 scale)
    payment_score = db.Column(NUMERIC(5, 2), default=0)  # Ödəniş intizamı
    property_score = db.Column(NUMERIC(5, 2), default=0)  # Əmlaka münasibət
    rental_history_score = db.Column(NUMERIC(5, 2), default=0)  # Əvvəlki icarə tarixçəsi
    neighbor_score = db.Column(NUMERIC(5, 2), default=0)  # Qonşularla və bina qaydalarına uyğunluq
    contract_score = db.Column(NUMERIC(5, 2), default=0)  # Müqavilə şərtlərinə uyğunluq
    
    # Final score (0-100 scale)
    total_score = db.Column(NUMERIC(5, 2), default=0)
    
    # Score interpretation
    score_category = db.Column(db.String(50), default='Yüksək riskli icarədar')
    
    # Detailed history
    payment_history = db.Column(JSONB)
    property_history = db.Column(JSONB)
    rental_history = db.Column(JSONB)
    neighbor_history = db.Column(JSONB)
    contract_history = db.Column(JSONB)
    
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    tenant = db.relationship('User', back_populates='tenant_score')

    def calculate_total_score(self):
        """Calculate weighted total score and convert to 100 scale"""
        weights = {
            'payment': 0.30,  # Ödəniş intizamı
            'property': 0.25,  # Əmlaka münasibət
            'history': 0.20,  # Əvvəlki icarə tarixçəsi
            'neighbor': 0.15,  # Qonşularla və bina qaydalarına uyğunluq
            'contract': 0.10   # Müqavilə şərtlərinə uyğunluq
        }
        
        # Calculate weighted average (0-5 scale)
        weighted_avg = (
            self.payment_score * weights['payment'] +
            self.property_score * weights['property'] +
            self.rental_history_score * weights['history'] +
            self.neighbor_score * weights['neighbor'] +
            self.contract_score * weights['contract']
        )
        
        # Convert to 100 scale
        self.total_score = (weighted_avg / 5) * 100
        
        # Determine score category
        if self.total_score >= 90:
            self.score_category = 'Çox etibarlı icarədar'
        elif self.total_score >= 75:
            self.score_category = 'Yaxşı icarədar'
        elif self.total_score >= 50:
            self.score_category = 'Orta riskli icarədar'
        else:
            self.score_category = 'Yüksək riskli icarədar'
        
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
        
        # Initialize score sums and counts
        scores = {
            'payment': {'sum': 0, 'count': 0},
            'property': {'sum': 0, 'count': 0},
            'history': {'sum': 0, 'count': 0},
            'neighbor': {'sum': 0, 'count': 0},
            'contract': {'sum': 0, 'count': 0}
        }
        
        # Sum up ratings for each component
        for rating in ratings:
            if rating.payment_score:
                scores['payment']['sum'] += rating.payment_score
                scores['payment']['count'] += 1
            if rating.property_score:
                scores['property']['sum'] += rating.property_score
                scores['property']['count'] += 1
            if rating.history_score:
                scores['history']['sum'] += rating.history_score
                scores['history']['count'] += 1
            if rating.neighbor_score:
                scores['neighbor']['sum'] += rating.neighbor_score
                scores['neighbor']['count'] += 1
            if rating.contract_score:
                scores['contract']['sum'] += rating.contract_score
                scores['contract']['count'] += 1
        
        # Calculate averages
        return {
            'payment_score': scores['payment']['sum'] / scores['payment']['count'] if scores['payment']['count'] > 0 else 0,
            'property_score': scores['property']['sum'] / scores['property']['count'] if scores['property']['count'] > 0 else 0,
            'rental_history_score': scores['history']['sum'] / scores['history']['count'] if scores['history']['count'] > 0 else 0,
            'neighbor_score': scores['neighbor']['sum'] / scores['neighbor']['count'] if scores['neighbor']['count'] > 0 else 0,
            'contract_score': scores['contract']['sum'] / scores['contract']['count'] if scores['contract']['count'] > 0 else 0
        }

class TenantQuestionnaire(db.Model):
    __tablename__ = 'tenant_questionnaires'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    age_group = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    marital_status = db.Column(db.String(20), nullable=False)
    dependents = db.Column(db.String(20), nullable=False)
    education = db.Column(db.String(20), nullable=False)
    work_sector = db.Column(db.String(50), nullable=False)
    work_experience = db.Column(db.String(20), nullable=False)
    credit_history = db.Column(db.String(50), nullable=False)
    monthly_income = db.Column(NUMERIC(10, 2), nullable=False)
    monthly_expenses = db.Column(NUMERIC(10, 2), nullable=False)
    planned_rent = db.Column(NUMERIC(10, 2), nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    
    # Relationships
    tenant = db.relationship('User', back_populates='questionnaire')

class RentalApplication(db.Model):
    __tablename__ = 'rental_applications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(application_status, nullable=False, default='pending')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Contract related fields
    contract_status = db.Column(contract_status, nullable=False, default='draft')
    contract_content = db.Column(db.Text)
    contract_generated_at = db.Column(db.DateTime(timezone=True))
    tenant_signature = db.Column(db.DateTime(timezone=True))
    landlord_signature = db.Column(db.DateTime(timezone=True))
    
    # Relationships
    tenant = db.relationship('User', back_populates='applications')
    rental_property = db.relationship('Property', back_populates='applications')
    ratings = db.relationship('Rating', back_populates='application', cascade='all, delete-orphan')
    contract = db.relationship('Contract', back_populates='application', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<RentalApplication {self.id}>'

class UserContractInfo(db.Model):
    __tablename__ = 'user_contract_info'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(20), nullable=False)
    fin = db.Column(db.String(20), nullable=False)
    birth_place = db.Column(db.String(200), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    user = db.relationship('User', back_populates='contract_info')

class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    application_id = db.Column(UUID(as_uuid=True), db.ForeignKey('rental_applications.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(NUMERIC(10, 2), nullable=False)
    status = db.Column(contract_status, nullable=False, default='draft')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    tenant = db.relationship('User', back_populates='contracts')
    property = db.relationship('Property', back_populates='contracts')
    application = db.relationship('RentalApplication', back_populates='contract')
    payments = db.relationship('Payment', back_populates='contract', cascade='all, delete-orphan')
    violations = db.relationship('ContractViolation', back_populates='contract', cascade='all, delete-orphan')

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(NUMERIC(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    status = db.Column(payment_status, nullable=False, default='pending')
    payment_method = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    contract = db.relationship('Contract', back_populates='payments')
    tenant = db.relationship('User', back_populates='payments')

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    severity = db.Column(complaint_severity, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(complaint_status, nullable=False, default='open')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    tenant = db.relationship('User', back_populates='complaints')
    property = db.relationship('Property')

class PropertyDamage(db.Model):
    __tablename__ = 'property_damages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    property_id = db.Column(UUID(as_uuid=True), db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    severity = db.Column(damage_severity, nullable=False)
    description = db.Column(db.Text, nullable=False)
    repair_cost = db.Column(NUMERIC(10, 2))
    status = db.Column(damage_status, nullable=False, default='reported')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    tenant = db.relationship('User', back_populates='damages')
    property = db.relationship('Property', back_populates='damages')

class ContractViolation(db.Model):
    __tablename__ = 'contract_violations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = db.Column(UUID(as_uuid=True), db.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    severity = db.Column(violation_severity, nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(violation_status, nullable=False, default='reported')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    contract = db.relationship('Contract', back_populates='violations')
    tenant = db.relationship('User', back_populates='violations')

# Event listeners
@event.listens_for(Payment, 'after_insert')
@event.listens_for(Payment, 'after_update')
def update_tenant_score_after_payment(mapper, connection, target):
    """Update tenant score after payment changes"""
    tenant_score = TenantScore.query.filter_by(tenant_id=target.tenant_id).first()
    if tenant_score:
        tenant_score.update_scores()
        db.session.commit()

@event.listens_for(Complaint, 'after_insert')
@event.listens_for(Complaint, 'after_update')
def update_tenant_score_after_complaint(mapper, connection, target):
    """Update tenant score after complaint changes"""
    tenant_score = TenantScore.query.filter_by(tenant_id=target.tenant_id).first()
    if tenant_score:
        tenant_score.update_scores()
        db.session.commit()

@event.listens_for(ContractViolation, 'after_insert')
@event.listens_for(ContractViolation, 'after_update')
def update_tenant_score_after_violation(mapper, connection, target):
    """Update tenant score after contract violation changes"""
    tenant_score = TenantScore.query.filter_by(tenant_id=target.tenant_id).first()
    if tenant_score:
        tenant_score.update_scores()
        db.session.commit()

@event.listens_for(RentalApplication, 'after_update')
def update_contract_status_after_signatures(mapper, connection, target):
    """Update contract status when both parties have signed"""
    if target.tenant_signature and target.landlord_signature and target.contract_status != 'active':
        target.contract_status = 'active'
        db.session.commit()