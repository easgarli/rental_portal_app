import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User
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
            tenant = User(
                email=tenant_data['email'],
                password_hash=generate_password_hash(tenant_data['password']),
                name=tenant_data['name'],
                role='tenant'
            )
            db.session.add(tenant)
        
        db.session.commit()
        
        print("\nTenants created successfully!")
        print("\nYou can now log in as any tenant with:")
        for tenant in tenants_data:
            print(f"\nName: {tenant['name']}")
            print(f"Email: {tenant['email']}")
            print(f"Password: {tenant['password']}")

if __name__ == '__main__':
    create_tenants() 