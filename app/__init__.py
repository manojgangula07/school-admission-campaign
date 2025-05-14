from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, generate_csrf
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
        from .models import Teacher, Student
        # db.create_all()  # Uncomment to create tables if necessary
        # print("Database tables created successfully!")

        # Example admin creation logic (optional)
        # admin = Teacher.query.filter_by(email="admin@admin.com").first()
        # if not admin:
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

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    # Bind extensions to app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)

    # ✅ Teardown: clean up SQLAlchemy sessions to avoid stale connections
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

    # ✅ Optional: Render healthcheck route
    @app.route('/ping')
    def ping():
        return 'pong', 200

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
