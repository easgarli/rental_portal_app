import sys
import os

# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from flask import Flask
from models import db, User
from app import create_app
from werkzeug.security import generate_password_hash

def create_tenants():
    """Create 4 tenants"""
    tenants_data = [
        {
            'email': 'tenant1@example.com',
            'password': 'password123',
            'name': 'Əli Məmmədov'
        },
        {
            'email': 'tenant2@example.com',
            'password': 'password123',
            'name': 'Leyla Əliyeva'
        },
        {
            'email': 'tenant3@example.com',
            'password': 'password123',
            'name': 'Vüsal Həsənli'
        },
        {
            'email': 'tenant4@example.com',
            'password': 'password123',
            'name': 'Aygün Kazımova'
        }
    ]

    app = create_app()
    with app.app_context():
        for tenant_data in tenants_data:
            # Check if tenant exists
            existing = User.query.filter_by(email=tenant_data['email']).first()
            if existing:
                print(f"Tenant {tenant_data['email']} already exists")
                continue

            tenant = User(
                email=tenant_data['email'],
                password=generate_password_hash(tenant_data['password']),  # Changed from password_hash
                name=tenant_data['name'],
                role='tenant'
            )
            try:
                db.session.add(tenant)
                print(f"Created tenant: {tenant_data['email']}")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating tenant {tenant_data['email']}: {str(e)}")

        db.session.commit()
        
        print("\nTenants created successfully!")
        print("\nYou can now log in as any tenant with:")
        for tenant in tenants_data:
            print(f"\nName: {tenant['name']}")
            print(f"Email: {tenant['email']}")
            print(f"Password: {tenant['password']}")

if __name__ == '__main__':
    create_tenants() 