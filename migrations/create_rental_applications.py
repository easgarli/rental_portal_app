from flask import Flask
from models import db, RentalApplication
from app import create_app

def run_migration():
    app = create_app()
    with app.app_context():
        # Create the rental_applications table
        db.create_all()
        print("Created rental_applications table successfully!")

if __name__ == "__main__":
    run_migration() 