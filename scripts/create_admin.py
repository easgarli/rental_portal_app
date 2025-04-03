import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

def create_admin_user(email, password, name):
    """Create an admin user"""
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email=email).first()
        if existing_admin:
            print(f"Admin user with email {email} already exists!")
            return

        # Create new admin user
        admin = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role='admin'
        )
        
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created successfully! Email: {email}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <email> <password> <name>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3]
    
    create_admin_user(email, password, name) 