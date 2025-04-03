import os
import sys
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User, Property
from werkzeug.security import generate_password_hash

def create_landlords():
    """Create 4 landlords"""
    landlords = []
    for i in range(1, 5):
        landlord = User(
            email=f'landlord{i}@example.com',
            password_hash=generate_password_hash('password123'),
            name=f'Landlord {i}',
            role='landlord'
        )
        db.session.add(landlord)
        landlords.append(landlord)
    
    db.session.commit()
    return landlords

def load_properties():
    """Load properties from JSON file"""
    with open('property_list.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def populate_db():
    """Populate database with landlords and properties"""
    app = create_app()
    with app.app_context():
        # Create landlords
        print("Creating landlords...")
        landlords = create_landlords()
        
        # Load properties
        properties_data = load_properties()
        
        print("Creating properties...")
        # Distribute properties among landlords (5 properties each)
        for i, prop_data in enumerate(properties_data):
            landlord = landlords[i // 5]  # Integer division to distribute evenly
            
            property = Property(
                landlord_id=landlord.id,
                title=prop_data['basliq'],
                description=prop_data['tesvir'],
                monthly_rent=prop_data['ayliq_icare'],
                address=prop_data['unvan'],
                available_from=datetime.strptime(prop_data['icareye_verilme_tarixi'], '%Y-%m-%d').date(),
                status='available'
            )
            db.session.add(property)
        
        db.session.commit()
        
        # Print summary
        print("\nDatabase populated successfully!")
        print("Created entities:")
        print(f"- 4 Landlords (landlord1@example.com to landlord4@example.com)")
        print(f"- {len(properties_data)} Properties distributed among landlords")
        print("\nYou can now log in as any landlord with:")
        print("Email: landlordN@example.com (where N is 1-4)")
        print("Password: password123")

if __name__ == '__main__':
    populate_db() 