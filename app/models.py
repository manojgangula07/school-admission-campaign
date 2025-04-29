from flask_login import UserMixin
from app import db

class Teacher(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512))
    mobile_number = db.Column(db.String(15), nullable=False)
    # Define the relationship here only
    students = db.relationship('Student', backref='teacher', lazy=True)

    def __repr__(self):
        return f"<Teacher {self.name}>"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    student_name = db.Column(db.String(256))
    father_name = db.Column(db.String(256))
    mother_name = db.Column(db.String(100))
    mobile_number = db.Column(db.String(15))
    student_class = db.Column(db.String(20))
    village = db.Column(db.String(256))
    previous_school = db.Column(db.String(100))
    remarks = db.Column(db.String(512))
    is_admitted = db.Column(db.Boolean, default=False)
    admission_date = db.Column(db.Date)
    follow_up_date = db.Column(db.Date)

    def __repr__(self):
        return f"<Student {self.student_name}>"
