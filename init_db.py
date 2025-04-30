import os
from app import create_app, db
from app.models import Teacher, Student  # Import your models

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
                admin = Teacher(
                    name="Admin",
                    email="admin@admin.com",
                    password="admin",  # In production, this should be hashed
                    mobile_number="0000000000"
                )
                db.session.add(admin)
                db.session.commit()
            
            print("Database initialized successfully!")
            print("Admin credentials:")
            print("Email: admin@admin.com")
            print("Password: admin")
            
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_database()