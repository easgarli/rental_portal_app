from flask import Flask
from models import db
from app import create_app

def reset_database():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all tables!")
        
        # Create all tables
        db.create_all()
        print("Created all tables!")

if __name__ == "__main__":
    reset_database() 