from flask import Flask
from config import Config, ProductionConfig
import os

def create_app():
    app = Flask(__name__)

    if os.getenv("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)

    # Initialize extensions like db here (e.g. db.init_app(app))

    return app

# Create the app instance and assign it to 'app'
app = create_app()
