from flask import Flask
from app import create_app, db

app = create_app()

@app.before_request
def create_tables():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True

if __name__ == '__main__':
    app.run(debug=True)
