from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from dotenv import load_dotenv
import os
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from utils.database import DatabaseConfig, DatabaseManager
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables first
load_dotenv()

def check_database():
    """Check if the application database exists, create it if it doesn't."""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=os.environ.get('POSTGRES_HOST', 'localhost'),
            port=os.environ.get('POSTGRES_PORT', '5432'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', ''),
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Get database name from environment variable
        db_name = os.environ.get('APP_DB')
        if not db_name:
            raise ValueError("APP_DB environment variable is not set")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create the database
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database {db_name} created successfully")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")
        raise

# Check database before app initialization
check_database()

# Import db first, then the models
from models import db
from models import User, Rating, TenantScore

from routes.auth import auth_bp
from routes.ratings import ratings_bp
from routes.tenant_score import tenant_score_bp
from routes.users import users_bp
from routes.properties import properties_bp
from routes.admin import admin_bp
from routes.questionnaire import questionnaire_bp
from routes.applications import applications_bp
from routes.tenant import tenant_bp
from routes.landlord import landlord_bp
from utils.csrf import init_csrf
from routes.payments import payments_bp
from routes.complaints import complaints_bp

def create_app():
    app = Flask(__name__)
    
    # Configure static files directory
    app.static_folder = 'static'
    
    # Configure app with fixed secret key
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_SECRET_KEY'] = 'csrf-secret-key'
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = False
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # We'll handle CSRF checks manually
    app.config['WTF_CSRF_FIELD_NAME'] = 'csrf_token'
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('APP_DB')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Initialize extensions
    init_csrf(app)  # Initialize CSRF first
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(ratings_bp, url_prefix='/ratings')
    app.register_blueprint(tenant_score_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questionnaire_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(landlord_bp)
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(complaints_bp, url_prefix='/complaints')

    # Add this near the top of create_app()
    app.template_folder = 'templates'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    with app.app_context():
        # Check if any of our tables exist
        inspector = db.inspect(db.engine)
        tables_to_check = [
            'users',                    # User model (base table with no foreign keys)
            'properties',               # Property model (depends on users)
            'tenant_questionnaires',    # TenantQuestionnaire model (depends on users)
            'tenant_scores',            # TenantScore model (depends on users)
            'ratings',                  # Rating model (depends on users and properties)
            'rental_applications',      # RentalApplication model (depends on users and properties)
            'user_contract_info',       # UserContractInfo model (depends on users)
            'contracts',                # Contract model (depends on users and properties)
            'payments',                 # Payment model (depends on contracts)
            'complaints',               # Complaint model (depends on users and properties)
            'property_damages',         # PropertyDamage model (depends on users and properties)
            'contract_violations'       # ContractViolation model (depends on contracts and users)
        ]
        missing_tables = [table for table in tables_to_check if not inspector.has_table(table)]
        
        if missing_tables:
            print(f"Creating missing tables: {', '.join(missing_tables)}")
            db.create_all()
            print("Database tables created!")
        else:
            print("All database tables exist!")

    # Main routes
    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            if current_user.role == 'tenant':
                return redirect(url_for('tenant.dashboard'))
            elif current_user.role == 'landlord':
                return redirect(url_for('landlord.dashboard'))
            else:
                return redirect(url_for('admin.dashboard'))
        except Exception as e:
            app.logger.error(f"Dashboard error: {str(e)}")
            return render_template('error.html', error="Dashboard yüklənərkən xəta baş verdi")

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # ... login logic ...
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                # Redirect based on role
                if user.role == 'tenant':
                    return redirect(url_for('tenant.dashboard'))
                elif user.role == 'landlord':
                    return redirect(url_for('landlord.dashboard'))
                else:
                    return redirect(url_for('admin.dashboard'))

    return app

if __name__ == '__main__':
    app = create_app()
    # run the app in debug mode with host 0.0.0.0 and port 8500
    app.run(debug=True) 