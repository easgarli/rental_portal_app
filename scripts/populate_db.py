import sys
import os

# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from flask import Flask
from models import db, User, Property
from app import create_app
from werkzeug.security import generate_password_hash
from datetime import datetime, UTC, date

def create_landlords():
    """Create 4 landlords"""
    landlords = []
    for i in range(1, 5):
        # Check if landlord exists
        email = f'landlord{i}@example.com'
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"Landlord {email} already exists")
            landlords.append(existing)
            continue

        landlord = User(
            email=email,
            password=generate_password_hash('password123'),  # Changed from password_hash
            name=f'Landlord {i}',
            role='landlord'
        )
        try:
            db.session.add(landlord)
            db.session.flush()  # Get ID before committing
            landlords.append(landlord)
            print(f"Created landlord: {email}")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating landlord {email}: {str(e)}")
            
    db.session.commit()
    return landlords

def create_properties(landlords):
    """Create sample properties"""
    properties_data = [
        {
            'title': '3 otaqlı mənzil, Nərimanov',
            'description': 'Təmirli, işıqlı mənzil',
            'address': 'Nərimanov r., Təbriz küç.',
            'monthly_rent': 800,
            'available_from': date.today(),
            'area': 95.5,
            'registry_number': 'N123456',
            'contract_term': 12
        },
        {
            'title': '2 otaqlı mənzil, Yasamal',
            'description': 'Yeni tikili, tam təmirli',
            'address': 'Yasamal r., Həsən bəy Zərdabi küç.',
            'monthly_rent': 650,
            'available_from': date.today(),
            'area': 78.0,
            'registry_number': 'Y789012',
            'contract_term': 12
        },
        {
            'title': '4 otaqlı mənzil, Xətai',
            'description': 'Geniş, işıqlı otaqlar, təmirli',
            'address': 'Xətai r., Sarayevo küç.',
            'monthly_rent': 1200,
            'available_from': date.today(),
            'area': 145.0,
            'registry_number': 'X345678',
            'contract_term': 12
        },
        {
            'title': '1 otaqlı mənzil, Nizami',
            'description': 'Studio tipli, əşyalı',
            'address': 'Nizami r., Qara Qarayev küç.',
            'monthly_rent': 450,
            'available_from': date.today(),
            'area': 42.0,
            'registry_number': 'NZ901234',
            'contract_term': 12
        },
        {
            'title': '3 otaqlı mənzil, Binəqədi',
            'description': 'Yeni təmirli, mərkəzi istilik',
            'address': 'Binəqədi r., 9-cu mikrorayon',
            'monthly_rent': 700,
            'available_from': date.today(),
            'area': 89.0,
            'registry_number': 'B567890',
            'contract_term': 12
        },
        {
            'title': '2 otaqlı mənzil, Nəsimi',
            'description': 'Mərkəzdə, tam təmirli',
            'address': 'Nəsimi r., Cavadxan küç.',
            'monthly_rent': 900,
            'available_from': date.today(),
            'area': 68.0,
            'registry_number': 'NS123789',
            'contract_term': 12
        },
        {
            'title': '4 otaqlı mənzil, Səbail',
            'description': 'Dəniz mənzərəli, premium təmirli',
            'address': 'Səbail r., Bayıl qəs.',
            'monthly_rent': 1500,
            'available_from': date.today(),
            'area': 158.0,
            'registry_number': 'S456123',
            'contract_term': 12
        },
        {
            'title': '1 otaqlı mənzil, 28 May',
            'description': 'Metro yaxınlığında, təmirli',
            'address': '28 May küç.',
            'monthly_rent': 500,
            'available_from': date.today(),
            'area': 45.0,
            'registry_number': 'M789456',
            'contract_term': 12
        }
    ]
    
    for i, data in enumerate(properties_data):
        # Distribute properties among landlords (2 properties each)
        landlord = landlords[i // 2]  # Integer division to distribute evenly
        
        property = Property(
            landlord_id=landlord.id,
            **data
        )
        try:
            db.session.add(property)
            print(f"Created property: {data['title']}")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating property {data['title']}: {str(e)}")
            
    db.session.commit()

def populate_db():
    """Populate database with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Creating landlords...")
        landlords = create_landlords()
        
        print("\nCreating properties...")
        create_properties(landlords)
        
        print("\nDatabase populated successfully!")
        print("Created entities:")
        print(f"- 4 Landlords (landlord1@example.com to landlord4@example.com)")
        print(f"- Properties distributed among landlords")
        print("\nYou can now log in as any landlord with:")
        print("Email: landlordN@example.com (where N is 1-4)")
        print("Password: password123")

if __name__ == '__main__':
    populate_db() 