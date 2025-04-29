from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config  # make sure this is imported

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import Teacher

    @login_manager.user_loader
    def load_user(user_id):
        return Teacher.query.get(int(user_id))

    from .routes import main
    app.register_blueprint(main)

    # ✅ Move your db upgrade logic here
    from flask_migrate import upgrade

    @app.before_first_request
    def apply_migrations():
        upgrade()

    return app
