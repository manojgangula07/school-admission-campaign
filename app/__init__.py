from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
from werkzeug.security import generate_password_hash
from flask_caching import Cache

# Initialize extensions (do not bind to app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache(config={'CACHE_TYPE': 'simple'})  # Use 'redis' or 'memcached' in production

# Set the login view for Flask-Login
login_manager.login_view = 'main.login'

def init_db(app):
    """Initialize the database and create admin account if it doesn't exist"""
    with app.app_context():
        # Import models here to avoid circular imports
        from .models import Teacher, Student
        
        # Create all tables
        #db.create_all()
        #print("Database tables created successfully!")
        
        # Check if admin exists
        # admin = Teacher.query.filter_by(email="admin@admin.com").first()
        # if not admin:
        #     # Create admin account if it doesn't exist
        #     admin = Teacher(
        #         name="Admin",
        #         email="admin@admin.com",
        #         password=generate_password_hash("admin"),
        #         mobile_number="0000000000"
        #     )
        #     db.session.add(admin)
        #     try:
        #         db.session.commit()
        #         print("Admin account created successfully!")
        #     except Exception as e:
        #         db.session.rollback()
        #         print(f"Error creating admin account: {e}")

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__, template_folder='templates')
    
    # Load app configuration
    app.config.from_object(Config)

    # Bind extensions to app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)

    # Setup user loader function for Flask-Login
    from .models import Teacher

    @login_manager.user_loader
    def load_user(user_id):
        return Teacher.query.get(int(user_id))

    # Register blueprints (for routing)
    from .routes import main
    app.register_blueprint(main)

    # Initialize database and create tables if needed
    init_db(app)

    return app
