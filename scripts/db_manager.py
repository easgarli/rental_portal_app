import sys
import os
from sqlalchemy.exc import SQLAlchemyError

# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from flask import Flask
from models import db
from app import create_app
from sqlalchemy import text

def reset_database():
    """Drop all tables and recreate them"""
    app = create_app()
    with app.app_context():
        try:
            # Drop all tables with CASCADE
            db.session.execute(text('DROP SCHEMA public CASCADE'))
            db.session.execute(text('CREATE SCHEMA public'))
            db.session.commit()
            print("Successfully dropped all tables!")
            
            # Create all tables
            db.create_all()
            print("Successfully created all tables!")
        except SQLAlchemyError as e:
            print(f"Error during database reset: {str(e)}")
            db.session.rollback()
            sys.exit(1)

def create_tables():
    """Create tables if they don't exist"""
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            print("Successfully created missing tables!")
        except SQLAlchemyError as e:
            print(f"Error creating tables: {str(e)}")
            db.session.rollback()
            sys.exit(1)

def drop_tables():
    """Drop all tables"""
    app = create_app()
    with app.app_context():
        try:
            # Drop all tables with CASCADE
            db.session.execute(text('DROP SCHEMA public CASCADE'))
            db.session.execute(text('CREATE SCHEMA public'))
            db.session.commit()
            print("Successfully dropped all tables!")
        except SQLAlchemyError as e:
            print(f"Error dropping tables: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management commands')
    parser.add_argument('command', choices=['reset', 'create', 'drop'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if args.command == 'reset':
        reset_database()
    elif args.command == 'create':
        create_tables()
    elif args.command == 'drop':
        drop_tables() 