from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Teacher, Student

main = Blueprint('main', __name__)

# Admin credentials
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin"

@main.route('/')
def home():
    return render_template('login.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('main.admin_dashboard'))
        
        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password, password):
            login_user(teacher)
            return redirect(url_for('main.teacher_dashboard'))
        
        flash('Invalid credentials')
        return redirect(url_for('main.login'))
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('admin', None)
    return redirect(url_for('main.login'))

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        mobile_number = request.form['mobile_number']
        
        new_teacher = Teacher(name=name, email=email, password=password, mobile_number=mobile_number)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Account created! Please log in.')
        return redirect(url_for('main.login'))
    
    return render_template('signup.html')

@main.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    students = Student.query.filter_by(teacher_id=current_user.id).all()
    
    # Get admission statistics
    admitted = Student.query.filter_by(teacher_id=current_user.id, is_admitted=True).count()
    not_admitted = Student.query.filter_by(teacher_id=current_user.id, is_admitted=False).count()
    
    # Get students per class
    class_stats = db.session.query(
        Student.student_class,
        func.count(Student.id)
    ).filter_by(teacher_id=current_user.id).group_by(Student.student_class).all()
    
    classes = [stat[0] for stat in class_stats]
    students_per_class = [stat[1] for stat in class_stats]
    
    # Get upcoming follow-ups (next 7 days)
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    upcoming_followups = Student.query.filter(
        Student.teacher_id == current_user.id,
        Student.is_admitted == False,
        Student.follow_up_date != None,
        Student.follow_up_date >= today,
        Student.follow_up_date <= next_week
    ).order_by(Student.follow_up_date).all()
    
    return render_template('teacher_dashboard.html', 
                         students=students,
                         admitted=admitted,
                         not_admitted=not_admitted,
                         classes=classes,
                         students_per_class=students_per_class,
                         upcoming_followups=upcoming_followups,
                         today=today)

@main.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    students = Student.query.all()
    teachers = Teacher.query.all()
    
    # Get unique classes and villages for filters
    classes = sorted(set(student.student_class for student in students))
    villages = sorted(set(student.village for student in students if student.village))
    
    students_by_teacher = db.session.query(Teacher.name, func.count(Student.id))\
        .join(Student).group_by(Teacher.name).all()

    students_by_class = db.session.query(Student.student_class, func.count(Student.id))\
        .group_by(Student.student_class).all()
    
    admitted_students = Student.query.filter_by(is_admitted=True).count()
    not_admitted_students = Student.query.filter_by(is_admitted=False).count()

    return render_template('admin_dashboard.html', 
                         students=students, 
                         teachers=teachers,
                         classes=classes,
                         villages=villages,
                         students_by_teacher=students_by_teacher,
                         students_by_class=students_by_class,
                         admitted=admitted_students,
                         not_admitted=not_admitted_students)

# Add, Edit, and Remove Teachers (Admin & Self-creation)

@main.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        name = request.form['name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        new_teacher = Teacher(name=name, mobile_number=mobile_number, email=email, password=password)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Teacher added successfully!')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('add_teacher.html')

@main.route('/add_teacher/self', methods=['GET', 'POST'])
def add_teacher_self():
    if session.get('teacher_id'):
        return redirect(url_for('main.teacher_dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        new_teacher = Teacher(name=name, mobile_number=mobile_number, email=email, password=password)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Account created successfully! Please log in.')
        return redirect(url_for('main.login'))
    
    return render_template('add_teacher.html')

@main.route('/delete_teacher/<int:id>', methods=['POST'])
def delete_teacher(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()
    
    flash('Teacher deleted successfully!')
    return redirect(url_for('main.admin_dashboard'))

# Add, Edit, and Remove Students

@main.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    is_admin = session.get('admin')
    
    teachers = Teacher.query.all() if is_admin else None

    if request.method == 'POST':
        teacher_id = None
        if is_admin:
            teacher_id_value = request.form.get('teacher_id')
            if teacher_id_value == 'admin':
                teacher_id = None  # No teacher assigned (admin's student)
            else:
                teacher_id = teacher_id_value
        else:
            teacher_id = current_user.id
        
        student = Student(
            student_name=request.form['student_name'],
            father_name=request.form.get('father_name'),
            mother_name=request.form.get('mother_name'),
            mobile_number=request.form['mobile_number'],
            student_class=request.form['student_class'],
            village=request.form.get('village'),
            previous_school=request.form.get('previous_school'),
            remarks=request.form.get('remarks'),
            teacher_id=teacher_id
        )
        db.session.add(student)
        db.session.commit()

        flash('Student added successfully!')
        return redirect(url_for('main.teacher_dashboard' if not is_admin else 'main.admin_dashboard'))
    
    return render_template('add_student.html', teachers=teachers, is_admin=is_admin)

@main.route('/edit_student/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    is_admin = session.get('admin')
    student = Student.query.get_or_404(id)
    
    if not is_admin and student.teacher_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('main.teacher_dashboard'))

    teachers = Teacher.query.all() if is_admin else None

    if request.method == 'POST':
        student.student_name = request.form['student_name']
        student.father_name = request.form.get('father_name')
        student.mother_name = request.form.get('mother_name')
        student.mobile_number = request.form['mobile_number']
        student.student_class = request.form['student_class']
        student.village = request.form.get('village')
        student.previous_school = request.form.get('previous_school')
        student.remarks = request.form.get('remarks')
        
        if is_admin:
            student.teacher_id = request.form.get('teacher_id')
        
        db.session.commit()

        flash('Student details updated successfully!')
        return redirect(url_for('main.teacher_dashboard' if not is_admin else 'admin_dashboard'))

    return render_template('edit_student.html', student=student, teachers=teachers, is_admin=is_admin)

@main.route('/admin/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    try:
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Student deleted successfully!'})
        else:
            flash('Student deleted successfully!')
            return redirect(url_for('main.admin_dashboard'))
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            flash('Error deleting student')
            return redirect(url_for('main.admin_dashboard'))

@main.route('/view_students')
@login_required
def view_students():
    is_admin = session.get('admin')
    if is_admin:
        students = Student.query.all()
    else:
        students = Student.query.filter_by(teacher_id=current_user.id).all()
    return render_template('view_students.html', students=students, is_admin=is_admin)

@main.route('/admin/edit_teacher/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    teacher = Teacher.query.get_or_404(id)
    
    if request.method == 'POST':
        teacher.name = request.form['name']
        teacher.email = request.form['email']
        teacher.mobile_number = request.form['mobile_number']
        if request.form.get('password'):
            teacher.password = generate_password_hash(request.form['password'])
        
        db.session.commit()
        flash('Teacher updated successfully!')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('edit_teacher.html', teacher=teacher)

@main.route('/admin/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student_admin(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    student = Student.query.get_or_404(id)
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        student.student_name = request.form['student_name']
        student.father_name = request.form.get('father_name')
        student.mother_name = request.form.get('mother_name')
        student.mobile_number = request.form['mobile_number']
        student.student_class = request.form['student_class']
        student.village = request.form.get('village')
        student.previous_school = request.form.get('previous_school')
        student.remarks = request.form.get('remarks')
        
        teacher_id_value = request.form.get('teacher_id')
        if teacher_id_value == 'admin':
            student.teacher_id = None  # No teacher assigned (admin's student)
        else:
            student.teacher_id = teacher_id_value
        
        is_admitted = request.form.get('is_admitted') == 'on'
        student.is_admitted = is_admitted
        
        if is_admitted:
            admission_date = request.form.get('admission_date')
            if admission_date:
                student.admission_date = datetime.strptime(admission_date, '%Y-%m-%d').date()
            elif not student.admission_date:
                student.admission_date = datetime.now().date()
        else:
            student.admission_date = None
        
        db.session.commit()
        flash('Student updated successfully!')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('edit_student_admin.html', student=student, teachers=teachers)

@main.route('/get_teachers')
def get_teachers():
    teachers = Teacher.query.all()
    return jsonify([{'id': t.id, 'name': t.name} for t in teachers])

@main.route('/admin/view_student/<int:id>')
def view_student(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    student = Student.query.get_or_404(id)
    return render_template('view_student.html', student=student)

@main.route('/admin/add_student', methods=['GET', 'POST'])
def add_student_admin():
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    teachers = Teacher.query.all()
    
    if request.method == 'POST':
        student = Student(
            student_name=request.form['student_name'],
            father_name=request.form.get('father_name'),
            mother_name=request.form.get('mother_name'),
            mobile_number=request.form['mobile_number'],
            student_class=request.form['student_class'],
            village=request.form.get('village'),
            previous_school=request.form.get('previous_school'),
            remarks=request.form.get('remarks'),
            teacher_id=request.form.get('teacher_id'),
            is_admitted=request.form.get('is_admitted') == 'on'
        )
        
        if student.is_admitted:
            admission_date = request.form.get('admission_date')
            if admission_date:
                student.admission_date = datetime.strptime(admission_date, '%Y-%m-%d').date()
            else:
                student.admission_date = datetime.now().date()
        
        db.session.add(student)
        db.session.commit()
        
        flash('Student added successfully!')
        return redirect(url_for('main.admin_dashboard'))
    
    return render_template('add_student_admin.html', teachers=teachers)

@main.route('/admin/teacher_stats/<int:teacher_id>')
def teacher_stats(teacher_id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # Get admission statistics
    admitted = Student.query.filter_by(teacher_id=teacher_id, is_admitted=True).count()
    not_admitted = Student.query.filter_by(teacher_id=teacher_id, is_admitted=False).count()
    
    # Get students per class
    class_stats = db.session.query(
        Student.student_class,
        func.count(Student.id)
    ).filter_by(teacher_id=teacher_id).group_by(Student.student_class).all()
    
    classes = [stat[0] for stat in class_stats]
    students_per_class = [stat[1] for stat in class_stats]
    
    return jsonify({
        'admitted': admitted,
        'not_admitted': not_admitted,
        'classes': classes,
        'students_per_class': students_per_class
    })

@main.route('/set_follow_up_date', methods=['POST'])
@login_required
def set_follow_up_date():
    data = request.get_json()
    student_id = data.get('student_id')
    follow_up_date = data.get('follow_up_date')
    
    if not student_id or not follow_up_date:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    student = Student.query.get_or_404(student_id)
    
    # Verify that the student belongs to the current teacher
    if student.teacher_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    try:
        student.follow_up_date = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@main.route('/reset-db')
def reset_db():
    db.drop_all()
    db.create_all()
    return "Database has been reset!"
