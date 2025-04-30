import os
from flask import Flask, render_template
from config import Config, ProductionConfig

def create_app():
    app = Flask(__name__)

    if os.getenv("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)

    # Initialize routes
    with app.app_context():
        from app import routes  # Ensure routes are correctly imported

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
