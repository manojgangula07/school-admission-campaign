import os
from app import create_app, db
from app.models import Teacher, Student  # Import your models
from werkzeug.security import generate_password_hash  # Import for password hashing

def init_database():
    try:
        app = create_app()
        with app.app_context():
            # Create all database tables
            db.create_all()
            
            # Check if admin exists
            admin = Teacher.query.filter_by(email="admin@admin.com").first()
            if not admin:
                print("Creating admin account...")
                # Create admin account if it doesn't exist
                hashed_password = generate_password_hash("admin")  # Hashing the password
                admin = Teacher(
                    name="Admin",
                    email="admin@admin.com",
                    password=hashed_password,  # Use hashed password in production
                    mobile_number="0000000000"
                )
                db.session.add(admin)
                db.session.commit()
            
            print("Database initialized successfully!")
            print("Admin credentials:")
            print("Email: admin@admin.com")
            print("Password: admin")  # Display plain password for first use (ensure to change this)
            
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_database()
