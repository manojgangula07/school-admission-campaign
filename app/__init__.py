from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config  # ✅ Import your config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__, template_folder='templates')
    
    app.config.from_object(Config)  # ✅ Load config from class (includes DATABASE_URL)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    from .models import Teacher
    
    @login_manager.user_loader
    def load_user(user_id):
        return Teacher.query.get(int(user_id))
    
    from .routes import main
    app.register_blueprint(main)
    
    with app.app_context():
        db.create_all()  # Optional if you're using Flask-Migrate later
    
    return app
