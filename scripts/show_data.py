import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Teacher, Student

# Create the app instance
app = create_app()

# Use app context to query the database
with app.app_context():
    # Query all teachers and students from the database
    teachers = Teacher.query.all()
    students = Student.query.all()

    # Print the results
    print("Teachers:")
    for t in teachers:
        print(f"ID: {t.id}, Name: {t.name}")  # Adjust according to your model's fields

    print("\nStudents:")
    for s in students:
        print(f"ID: {s.id}, Name: {s.name}")  # Adjust according to your model's fields
