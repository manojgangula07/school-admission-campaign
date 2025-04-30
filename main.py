from flask import Flask
from config import Config, ProductionConfig

def create_app():
    app = Flask(__name__)

    if os.getenv("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)

    # Initialize extensions like db here
    return app
