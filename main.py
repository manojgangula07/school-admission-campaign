from flask import Flask
from config import Config, ProductionConfig
import os

def create_app():
    app = Flask(__name__)

    if os.getenv("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)

    # Define a route for the root URL
    @app.route('/')
    def index():
        return "Welcome to the School Admission Campaign!"

    return app

app = create_app()
