from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional
from app.models import Teacher,Student
from wtforms.fields import SelectField, HiddenField

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    mobile_number = StringField('Mobile Number', validators=[DataRequired()])

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Length

class AddStudentForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    father_name = StringField('Father Name', validators=[DataRequired(), Length(max=100)])
    mother_name = StringField('Mother Name', validators=[DataRequired(), Length(max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(max=15)])
    student_class = SelectField('Class', choices=[
        ('NUR', 'NUR'), ('LKG', 'LKG'), ('UKG', 'UKG'), ('1', '1'), ('2', '2'), ('3', '3'), 
        ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')
    ], validators=[DataRequired()])
    village = StringField('Village', validators=[Length(max=100)])
    previous_school = StringField('Previous School', validators=[Length(max=100)])
    remarks = StringField('Remarks', validators=[Length(max=255)])
    is_admitted = BooleanField('Is Admitted?')
    teacher_id = SelectField('Assign Teacher', coerce=int)
    submit = SubmitField('Add Student')

    class Meta:
        # No need for csrf_class here
        pass

class StudentForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    father_name = StringField('Father Name', validators=[DataRequired(), Length(max=100)])
    mother_name = StringField('Mother Name', validators=[DataRequired(), Length(max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(max=15)])
    student_class = SelectField('Class', choices=[
        ('NUR', 'NUR'), ('LKG', 'LKG'), ('UKG', 'UKG'), ('1', '1'), ('2', '2'), ('3', '3'), 
        ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')
    ], validators=[DataRequired()])
    village = StringField('Village', validators=[Length(max=100)])
    previous_school = StringField('Previous School', validators=[Length(max=100)])
    remarks = StringField('Remarks', validators=[Length(max=255)])


class EditStudentForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(min=1, max=100)])
    father_name = StringField('Father Name', validators=[Length(max=100)])
    mother_name = StringField('Mother Name', validators=[Length(max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(min=10, max=15)])
    student_class = SelectField('Class', choices=[
        ('NUR', 'NUR'), ('LKG', 'LKG'), ('UKG', 'UKG'), ('1', '1'), ('2', '2'), ('3', '3'), 
        ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')
    ], validators=[DataRequired()])
    village = StringField('Village', validators=[Length(max=100)])
    previous_school = StringField('Previous School', validators=[Length(max=100)])
    remarks = TextAreaField('Remarks', validators=[Length(max=500)])

    # Assign Teacher (choices will be set dynamically in the route)
    teacher_id = SelectField('Assign Teacher', coerce=int, validators=[DataRequired()])

    # Checkbox for admission status
    is_admitted = BooleanField('Mark as Admitted')

    # Admission Date (only shown if student is admitted)
    admission_date = DateField('Admission Date', format='%Y-%m-%d', validators=[Optional()])

    class Meta:
        csrf = True

    # Dynamically populate teacher choices in the form constructor
    def __init__(self, *args, **kwargs):
        super(EditStudentForm, self).__init__(*args, **kwargs)
        
        # Dynamically set teacher choices
        self.teacher_id.choices = [(teacher.id, teacher.name) for teacher in Teacher.query.all()]  # Adjust Teacher model attributes if needed%d')

        
   
class EditTeacherForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_number = StringField('mobile_number', validators=[DataRequired(), Length(min=10, max=15)])
   
    
    submit = SubmitField('Update')

class AddStudentByTeacherForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    father_name = StringField('Father Name', validators=[DataRequired(), Length(max=100)])
    mother_name = StringField('Mother Name', validators=[DataRequired(), Length(max=100)])
    mobile_number = StringField('Mobile Number', validators=[DataRequired(), Length(max=15)])
    student_class = SelectField('Class', choices=[
        ('NUR', 'NUR'), ('LKG', 'LKG'), ('UKG', 'UKG'), ('1', '1'), ('2', '2'), ('3', '3'), 
        ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10')
    ], validators=[DataRequired()])
    village = StringField('Village', validators=[Length(max=100)])
    previous_school = StringField('Previous School', validators=[Length(max=100)])
    remarks = StringField('Remarks', validators=[Length(max=255)])
    teacher_id = HiddenField()  # Hidden field to store the teacher's ID automatically
    submit = SubmitField('Add Student')
   