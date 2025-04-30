from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
import os
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
csrf = CSRFProtect()

def init_db(app):
    """Initialize the database and create admin account if it doesn't exist"""
    with app.app_context():
        # Import models here to avoid circular imports
        from .models import Teacher, Student
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if admin exists
        admin = Teacher.query.filter_by(email="admin@admin.com").first()
        if not admin:
            # Create admin account
            admin = Teacher(
                name="Admin",
                email="admin@admin.com",
                password=generate_password_hash("admin"),
                mobile_number="0000000000"
            )
            db.session.add(admin)
            try:
                db.session.commit()
                print("Admin account created successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating admin account: {e}")

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import Teacher

    @login_manager.user_loader
    def load_user(user_id):
        return Teacher.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)

    # Initialize database and create tables
    init_db(app)

    return app
