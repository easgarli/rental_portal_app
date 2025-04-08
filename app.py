from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, send_from_directory
from flask_login import LoginManager, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from dotenv import load_dotenv
import os

# Load environment variables first
load_dotenv()

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
from utils.csrf import init_csrf

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
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
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
    app.register_blueprint(ratings_bp)
    app.register_blueprint(tenant_score_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questionnaire_bp)
    app.register_blueprint(applications_bp)

    # Add this near the top of create_app()
    app.template_folder = 'templates'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    with app.app_context():
        # Check if any of our tables exist
        inspector = db.inspect(db.engine)
        tables_to_check = [
            'users',                    # User model
            'ratings',                  # Rating model
            'properties',               # Property model
            'tenant_questionnaires',    # TenantQuestionnaire model
            'rental_applications',      # RentalApplication model
            'user_contract_info',       # UserContractInfo model
            'tenant_scores'             # TenantScore model
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
            if current_user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif current_user.role == 'tenant':
                return render_template('dashboard/tenant.html')
            else:
                return render_template('dashboard/landlord.html')
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
            return render_template('error.html', error=str(e)), 500

    @app.route('/about')
    def about():
        return render_template('about.html')


    return app

if __name__ == '__main__':
    app = create_app()
    # run the app in debug mode with host 0.0.0.0 and port 8500
    app.run(debug=True) 