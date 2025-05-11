from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, Response, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, case
from flask_login import login_user, logout_user, login_required, current_user
from app import db, cache
from app.models import Teacher, Student
from .forms import SignupForm, EditStudentForm ,EditTeacherForm, AddStudentForm, AddStudentByTeacherForm
from flask import Blueprint
import csv
from sqlalchemy.orm import joinedload
import io
import openpyxl
from flask_caching import Cache
from flask import current_app

main = Blueprint('main', __name__)

import os
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

@main.route('/')
def home():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session data and cache
    session.clear()
    cache.clear()
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin'] = True
            session['user_type'] = 'admin'
            return redirect(url_for('main.admin_dashboard'))
        
        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password, password):
            login_user(teacher)
            session['teacher_id'] = teacher.id
            session['user_type'] = 'teacher'
            return redirect(url_for('main.teacher_dashboard'))
        
        flash('Invalid credentials')
        return redirect(url_for('main.login'))
    
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    # Clear all session data
    session.clear()
    # Clear any cached data
    cache.clear()
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = generate_password_hash(form.password.data)
        mobile_number = form.mobile_number.data
        
        new_teacher = Teacher(name=name, email=email, password=password, mobile_number=mobile_number)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Account created! Please log in.')
        return redirect(url_for('main.login'))
    
    return render_template('signup.html', form=form)

@main.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    # Get all students for this teacher
    students = Student.query.filter_by(teacher_id=current_user.id).all()
    
    stats = db.session.query(
        func.sum(case((Student.is_admitted == True, 1), else_=0)).label('admitted'),
        func.sum(case((Student.is_admitted == False, 1), else_=0)).label('not_admitted'),
        Student.student_class,
        func.count(Student.id)
    ).filter_by(teacher_id=current_user.id).group_by(Student.student_class).all()

    admitted = sum(row[0] for row in stats)
    not_admitted = sum(row[1] for row in stats)
    classes = [row[2] for row in stats]
    students_per_class = [row[3] for row in stats]

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

from flask import request

# Optimized admin_dashboard route with async teacher stats and paginated duplicates
@main.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('main.login'))

    # Get cached stats for the four charts
    stats = get_admin_dashboard_stats()

    return render_template('admin_dashboard.html',
        students_by_teacher=stats['students_by_teacher'],
        students_by_class=stats['students_by_class'],
        admitted_class_counts=stats['admitted_class_counts'],
        not_admitted_class_counts=stats['not_admitted_class_counts'],
        students_by_class_labels=stats['sorted_classes'],
        admission_stats={"Admitted": stats['admitted_count'], "Not Admitted": stats['not_admitted_count']},
        admitted=stats['admitted_count'],
        not_admitted=stats['not_admitted_count'],
        village_counts=stats['village_counts'],
        villages=stats['villages'],
    )

def compute_admin_dashboard_stats():
    # Students by teacher
    students_by_teacher = db.session.query(Teacher.name, func.count(Student.id))\
        .join(Student).group_by(Teacher.name)\
        .order_by(func.count(Student.id).desc()).all()

    # Class stats in one query
    class_stats = db.session.query(
        Student.student_class,
        Student.is_admitted,
        func.count(Student.id)
    ).filter(Student.student_class.isnot(None))\
     .group_by(Student.student_class, Student.is_admitted).all()

    class_order = ['NUR', 'LKG', 'UKG'] + [str(i) for i in range(1, 10)]
    stats_dict = {(cls, adm): count for cls, adm, count in class_stats}
    sorted_classes = sorted(set(cls for cls, _, _ in class_stats),
                            key=lambda x: class_order.index(x) if x in class_order else len(class_order))
    admitted_class_counts = [stats_dict.get((cls, True), 0) for cls in sorted_classes]
    not_admitted_class_counts = [stats_dict.get((cls, False), 0) for cls in sorted_classes]
    students_by_class = list(zip(sorted_classes, [a + b for a, b in zip(admitted_class_counts, not_admitted_class_counts)]))

    admitted_count = sum(admitted_class_counts)
    not_admitted_count = sum(not_admitted_class_counts)

    # Get village statistics
    village_stats = db.session.query(
        Student.village,
        func.count(Student.id)
    ).filter(Student.village.isnot(None))\
     .group_by(Student.village)\
     .order_by(func.count(Student.id).desc()).all()

    village_counts = [stat[1] for stat in village_stats]
    villages = [stat[0] for stat in village_stats]

    return {
        'students_by_teacher': students_by_teacher,
        'class_stats': class_stats,
        'class_order': class_order,
        'stats_dict': stats_dict,
        'sorted_classes': sorted_classes,
        'admitted_class_counts': admitted_class_counts,
        'not_admitted_class_counts': not_admitted_class_counts,
        'students_by_class': students_by_class,
        'admitted_count': admitted_count,
        'not_admitted_count': not_admitted_count,
        'village_counts': village_counts,
        'villages': villages,
    }

@cache.cached(timeout=300, key_prefix='admin_dashboard_stats')
def get_admin_dashboard_stats():
    return compute_admin_dashboard_stats()

@main.route('/admin/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    # Clear any existing flash messages
    session.pop('_flashes', None)
    
    if request.method == 'POST':
        name = request.form['name']
        mobile_number = request.form['mobile_number']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        new_teacher = Teacher(name=name, mobile_number=mobile_number, email=email, password=password)
        db.session.add(new_teacher)
        db.session.commit()
        
        flash('Teacher added successfully!')
        return redirect(url_for('main.teacher_management'))
    
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

@main.route('/admin/delete_teacher/<int:id>', methods=['POST'])
def delete_teacher(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    try:
        teacher = Teacher.query.get_or_404(id)
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher deleted successfully!', 'success')
        return redirect(url_for('main.teacher_management'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting teacher: {str(e)}', 'danger')
        return redirect(url_for('main.teacher_management'))

# Add, Edit, and Remove Students

@main.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    form = AddStudentByTeacherForm()

    # Automatically assign the logged-in teacher's ID to the teacher_id field
    form.teacher_id.data = current_user.id

    if form.validate_on_submit():
        # Normalize village only
        cleaned_village = form.village.data.strip().title() if form.village.data else None

        student = Student(
            student_name=form.student_name.data,
            father_name=form.father_name.data,
            mother_name=form.mother_name.data,
            mobile_number=form.mobile_number.data,
            student_class=form.student_class.data,
            village=cleaned_village,
            previous_school=form.previous_school.data,
            remarks=form.remarks.data,
            teacher_id=form.teacher_id.data
        )

        db.session.add(student)
        try:
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('main.teacher_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')

    return render_template('add_student.html', form=form)



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
        try:
            student.student_name = request.form['student_name']
            student.father_name = request.form.get('father_name')
            student.mother_name = request.form.get('mother_name')
            student.mobile_number = request.form['mobile_number']
            student.student_class = request.form['student_class']
            student.village = request.form.get('village')
            student.previous_school = request.form.get('previous_school')
            student.remarks = request.form.get('remarks')
            
            # Handle admission status
            student.is_admitted = request.form.get('is_admitted') == 'on'
            if student.is_admitted:
                admission_date = request.form.get('admission_date')
                if admission_date:
                    student.admission_date = datetime.strptime(admission_date, '%Y-%m-%d').date()
                elif not student.admission_date:
                    student.admission_date = datetime.now().date()
            else:
                student.admission_date = None
            
            db.session.commit()
            flash('Student details updated successfully!')
            
            return redirect(url_for('main.teacher_dashboard' if not is_admin else 'main.admission_campaign'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}')
            return render_template('edit_student.html', student=student, teachers=teachers, is_admin=is_admin)

    return render_template('edit_student.html', student=student, teachers=teachers, is_admin=is_admin)

@main.route('/admin/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if not session.get('admin'):
        return redirect(url_for('main.login'))
    
    try:
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting student: ' + str(e))
    
    return redirect(url_for('main.admission_campaign'))

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
    form = EditTeacherForm(obj=teacher)  # Pre-fill form with existing data

    if form.validate_on_submit():
        teacher.name = form.name.data
        teacher.email = form.email.data
        teacher.mobile_number = form.mobile_number.data  # assuming form.phone maps to model.mobile_number
        if request.form.get('password'):
            teacher.password = generate_password_hash(request.form['password'])

        db.session.commit()
        flash('Teacher updated successfully!')
        return redirect(url_for('main.teacher_management'))
    
    return render_template('edit_teacher.html', form=form, teacher=teacher)

@main.route('/admin/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student_admin(id):
    student = Student.query.get_or_404(id)

    # Dynamically populate teacher choices
    teacher_choices = [(teacher.id, teacher.name) for teacher in Teacher.query.all()]

    if request.method == 'POST':
        form = EditStudentForm(request.form)
        form.teacher_id.choices = teacher_choices

        if form.validate():
            student.student_name = form.student_name.data
            student.father_name = form.father_name.data
            student.mother_name = form.mother_name.data
            student.mobile_number = form.mobile_number.data
            student.student_class = form.student_class.data
            student.village = form.village.data.strip().title() if form.village.data else None  # Normalize
            student.previous_school = form.previous_school.data
            student.remarks = form.remarks.data

            # Teacher assignment
            student.teacher_id = form.teacher_id.data

            # Admission checkbox + date
            student.is_admitted = form.is_admitted.data
            if form.is_admitted.data:
                student.admission_date = form.admission_date.data or datetime.now().date()
            else:
                student.admission_date = None

            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('main.admission_campaign'))
        else:
            flash('Form validation failed. Please check all required fields.', 'danger')
    else:
        form = EditStudentForm(obj=student)
        form.teacher_id.choices = teacher_choices
        # Populate boolean and date manually if needed
        form.is_admitted.data = student.is_admitted
        form.admission_date.data = student.admission_date

    return render_template('edit_student_admin.html', form=form, student=student, is_admin=True)



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

from datetime import datetime

@main.route('/admin/add_student', methods=['GET', 'POST'])
def add_student_admin():
    if not session.get('admin'):
        return redirect(url_for('main.login'))

    form = AddStudentForm()

    # Dynamically set teacher choices
    teachers = Teacher.query.all()
    form.teacher_id.choices = [(teacher.id, teacher.name) for teacher in teachers] if teachers else [(None, 'No teachers available')]

    if form.validate_on_submit():
        cleaned_village = form.village.data.strip().title() if form.village.data else None

        try:
            student = Student(
                student_name=form.student_name.data,
                father_name=form.father_name.data,
                mother_name=form.mother_name.data,
                mobile_number=form.mobile_number.data,
                student_class=form.student_class.data,
                village=cleaned_village,
                previous_school=form.previous_school.data,
                remarks=form.remarks.data,
                is_admitted=form.is_admitted.data,
                teacher_id=form.teacher_id.data if form.teacher_id.data else None
            )

            # Set admission date only if admitted
            if form.is_admitted.data:
                student.admission_date = datetime.now().date()  # Automatically set today's date

            db.session.add(student)
            db.session.commit()

            flash('Student added successfully!', 'success')
            return redirect(url_for('main.admission_campaign'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'danger')

    return render_template('add_student_admin.html', form=form, teachers=teachers)


 

@main.route('/admin/teacher_stats/<int:teacher_id>')
def teacher_stats(teacher_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401
    
    try:
        teacher = Teacher.query.get_or_404(teacher_id)
        
        # Get admission statistics
        admitted = Student.query.filter_by(teacher_id=teacher_id, is_admitted=True).count()
        not_admitted = Student.query.filter_by(teacher_id=teacher_id, is_admitted=False).count()
        
        # Get students per class
        class_stats = db.session.query(
            Student.student_class,
            func.count(Student.id)
        ).filter_by(teacher_id=teacher_id).group_by(Student.student_class).all()
        
        # Format class stats as list of tuples
        class_stats_list = [(str(cls), count) for cls, count in class_stats]
        
        return jsonify({
            'success': True,
            'admitted': admitted,
            'not_admitted': not_admitted,
            'class_stats': class_stats_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@main.route('/set_follow_up_date', methods=['POST'])
@login_required
def set_follow_up_date():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        follow_up_date = data.get('follow_up_date')
        
        if not student_id or not follow_up_date:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        student = Student.query.get_or_404(student_id)
        
        # Allow both admin and the assigned teacher to set follow-up date
        if not session.get('admin') and student.teacher_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized access'})
        
        student.follow_up_date = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Follow-up date set successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@main.route('/admin/teacher_management', methods=['GET'])
def teacher_management():
    if not session.get('admin'):
        return redirect(url_for('main.login'))

    # Fetch all teachers
    all_teachers = Teacher.query.all()

    # Fetch teacher IDs
    teacher_ids = [t.id for t in all_teachers]

    # Get admission statistics for each teacher
    teacher_stats = {}
    for teacher in all_teachers:
        admitted = Student.query.filter_by(teacher_id=teacher.id, is_admitted=True).count()
        not_admitted = Student.query.filter_by(teacher_id=teacher.id, is_admitted=False).count()
        
        # Get class distribution
        class_stats = db.session.query(
            Student.student_class,
            func.count(Student.id)
        ).filter_by(teacher_id=teacher.id).group_by(Student.student_class).all()
        
        teacher_stats[teacher.id] = {
            'admitted': admitted,
            'not_admitted': not_admitted,
            'class_stats': [(str(cls), count) for cls, count in class_stats]
        }

    return render_template('teacher_management.html', 
                         teachers=all_teachers, 
                         teacher_stats=teacher_stats)

@main.route('/admission_campaign')
def admission_campaign():
    if not session.get('admin'):
        return redirect(url_for('main.login'))

    # Pagination setup
    page = request.args.get('page', 1, type=int)
    page_duplicates = request.args.get('page_duplicates', 1, type=int)
    students_per_page = 30
    duplicates_per_page = 30

    # Get active tab
    active_tab = request.args.get('active_tab', 'students')

    # Filters
    search_name = request.args.get('search_name', '').strip()
    class_filter = request.args.get('class_filter', '').strip()
    village_filter = request.args.get('village_filter', '').strip()
    teacher_filter = request.args.get('teacher_filter', '').strip()

    # Student filtering query
    student_query = Student.query
    if search_name:
        student_query = student_query.filter(Student.student_name.ilike(f"%{search_name}%"))
    if class_filter:
        student_query = student_query.filter(Student.student_class == class_filter)
    if village_filter:
        student_query = student_query.filter(Student.village == village_filter)
    if teacher_filter:
        try:
            teacher_id = int(teacher_filter)
            student_query = student_query.filter(Student.teacher_id == teacher_id)
        except ValueError:
            pass

    # Paginated students
    students = student_query.order_by(Student.id.desc()).paginate(
        page=page, per_page=students_per_page, error_out=False
    )

    # Filter options
    all_teachers = Teacher.query.all()
    classes = [c[0] for c in db.session.query(Student.student_class)
               .distinct().filter(Student.student_class.isnot(None)).all()]
    villages = sorted({v[0].strip().title() for v in db.session.query(Student.village)
                       .filter(Student.village.isnot(None)).all() if v[0]})

    # Duplicate detection: scoped and paginated
    dup_subquery = db.session.query(
        Student.student_class,
        Student.village,
        Student.mobile_number
    ).filter(Student.mobile_number.isnot(None), Student.village.isnot(None), Student.student_class.isnot(None))\
     .group_by(Student.student_class, Student.village, Student.mobile_number)\
     .having(func.count(func.distinct(Student.teacher_id)) > 1).subquery()

    duplicate_query = db.session.query(Student).join(
        dup_subquery,
        (Student.student_class == dup_subquery.c.student_class) &
        (Student.village == dup_subquery.c.village) &
        (Student.mobile_number == dup_subquery.c.mobile_number)
    ).order_by(Student.student_name)

    duplicates = duplicate_query.paginate(
        page=page_duplicates, per_page=duplicates_per_page, error_out=False
    )

    return render_template('admission_campaign.html',
                         students=students,
                         duplicates=duplicates,
                         all_teachers=all_teachers,
                         classes=classes,
                         villages=villages,
                         search_name=search_name,
                         class_filter=class_filter,
                         village_filter=village_filter,
                         teacher_filter=teacher_filter,
                         active_tab=active_tab)

@main.route('/export_students')
def export_students():
    if not session.get('admin'):
        return redirect(url_for('main.login'))

    # Get filters from query params
    search_name = request.args.get('search_name', '').strip()
    class_filter = request.args.get('class_filter', '').strip()
    village_filter = request.args.get('village_filter', '').strip()
    teacher_filter = request.args.get('teacher_filter', '').strip()

    # Student filtering query (same as in admission_campaign)
    student_query = Student.query.options(joinedload(Student.teacher))
    if search_name:
        student_query = student_query.filter(Student.student_name.ilike(f"%{search_name}%"))
    if class_filter:
        student_query = student_query.filter(Student.student_class == class_filter)
    if village_filter:
        student_query = student_query.filter(Student.village == village_filter)
    if teacher_filter:
        try:
            teacher_id = int(teacher_filter)
            student_query = student_query.filter(Student.teacher_id == teacher_id)
        except ValueError:
            pass

    students = student_query.order_by(Student.id.desc()).all()

    # Create Excel workbook in memory
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # Write header
    header = ['ID', 'Name', 'Father', 'Village', 'Mobile', 'Class', 'Teacher', 'Status', 'Admission Date']
    ws.append(header)

    # Write data rows
    for s in students:
        ws.append([
            s.id,
            s.student_name or '',
            s.father_name or '',
            s.village or '',
            s.mobile_number or '',
            s.student_class or '',
            s.teacher.name if s.teacher else '',
            'Admitted' if s.is_admitted else 'Not Admitted',
            s.admission_date.strftime('%Y-%m-%d') if s.admission_date else ''
        ])

    # Save to a BytesIO buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name='students.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



