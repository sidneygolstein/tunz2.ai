from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, session, jsonify
from app import db, mail
from app.models.hr import HR
from app.models.company import Company
from app.models.interview import Interview
from app.models.interview_parameter import InterviewParameter
from app.models.admin import Admin
from app.models.session import Session
from app.models.review_question import ReviewQuestion
from flask_mail import Message
from datetime import datetime
from app.decorators import admin_required
from sqlalchemy import func
from helpers import get_url

admin = Blueprint('admin', __name__)

@admin.route('/home', methods=['GET'])
@admin_required
def home():
    admin_id = session.get('admin_id')
    if not admin_id:
        flash('Please log in to access the admin dashboard.', 'danger')
        return redirect(url_for('auth.admin_login'))

    admin = Admin.query.get(admin_id)
    if not admin:
        flash('Admin not found.', 'danger')
        return redirect(url_for('auth.admin_login'))
    hrs = HR.query.all()
    total_hr = HR.query.count()
    total_interviews = Interview.query.count()
    total_sessions = Session.query.count()

    # Ensure created_at is datetime object (if needed)
    for hr in hrs:
        if isinstance(hr.created_at, str):
            hr.created_at = datetime.strptime(hr.created_at, '%Y-%m-%d')
    
    # Fetch mean ratings per question
    questions = ReviewQuestion.query.with_entities(ReviewQuestion.text).distinct().all()
    question_ratings = {}
    for question in questions:
        avg_rating = db.session.query(func.avg(ReviewQuestion.rating)).filter(ReviewQuestion.text == question.text).scalar()
        rating_count = db.session.query(func.count(ReviewQuestion.rating)).filter(ReviewQuestion.text == question.text).scalar()
        question_ratings[question.text] = {
            'avg_rating': avg_rating,
            'rating_count': rating_count
        }


    # Fetch interviews and sessions count for each HR
    hr_interview_session_data = []
    for hr in hrs:
        interview_count = Interview.query.filter_by(hr_id=hr.id).count()
        session_count = db.session.query(Session).join(InterviewParameter).join(Interview).filter(Interview.hr_id == hr.id).count()
        hr_interview_session_data.append({
            'hr': hr,
            'interview_count': interview_count,
            'session_count': session_count
        }) 

    return render_template('admin/admin_homepage.html', admin=admin, hrs=hrs, 
                           total_hr=total_hr, total_interviews=total_interviews, 
                           total_sessions=total_sessions, question_ratings=question_ratings,
                           hr_interview_session_data=hr_interview_session_data)



@admin.route('/confirm/<int:hr_id>', methods=['GET', 'POST'])
@admin_required
def confirm_account(hr_id):
    admin_id = request.form.get('admin_id')  # Get admin_id from session set by the decorator
    print(f"admin_id from session: {admin_id}")

    hrs = HR.query.get(hr_id)
    if not hrs:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.home', admin_id=admin_id))
    

    return render_template('admin/admin_account_confirmation.html', email=hrs.email, name=hrs.name, surname=hrs.surname, company_name=hrs.company.name, hr_id=hrs.id, admin_id=admin_id)


@admin.route('/accept/<int:hr_id>', methods=['POST'])
@admin_required
def accept_account(hr_id):
    admin_id = request.form.get('admin_id')  # Get admin_id from session set by the decorator
    if not admin_id:
        return jsonify({"msg": "Admin ID missing from form data"}), 400
    user = HR.query.get_or_404(hr_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.home', admin_id=admin_id))
    user.confirmed = True
    db.session.commit()

    # Send email to HR confirming account activation
    msg = Message('Tunz.ai Account Confirmation',
                  sender='noreply@tunz.ai',
                  recipients=[user.email])
    url = get_url('auth.login')
    # {url_for('auth.login', _external=True, _scheme='https')} 
    msg.body = f'Hello {user.name}, \n\nWe have just confirmed your account! You are all set, lets get you started and create your first AI interviews to send to applicants!\nTo login, just go to: {url} \n\nThanks a lot! \nThe Tunz AI team'
    mail.send(msg)
    return redirect(url_for('admin.home', admin_id=admin_id))

@admin.route('/deny/<int:hr_id>', methods=['POST'])
@admin_required
def deny_account(hr_id):
    user = HR.query.get_or_404(hr_id)
    admin_id = request.form.get('admin_id')  # Get admin_id from session set by the decorator
    if not admin_id:
        return jsonify({"msg": "Admin ID missing from form data"}), 400
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.home', admin_id=admin_id))
    
    # Send email to HR denying account activation
    msg = Message('Account Denied',
                  sender='noreply@tunz.ai',
                  recipients=[user.email])
    msg.body = f'Your account has been denied by the admin. You cannot login. If you have any question, please contact: sidney@tunz.ai or sebastien@tunz.ai .'
    mail.send(msg)

    db.session.delete(user)
    db.session.commit()

    
    return redirect(url_for('admin.home', admin_id=admin_id))

@admin.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('admin_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.admin_login'))



@admin.route('/delete_hr/<int:hr_id>', methods=['POST'])
@admin_required
def delete_hr(hr_id):
    hr = HR.query.get_or_404(hr_id)
    db.session.delete(hr)
    db.session.commit()
    flash('HR deleted successfully.', 'success')
    return redirect(url_for('admin.home'))



@admin.route('/view_hr_info/<int:hr_id>', methods=['GET'])
@admin_required
def view_hr_info(hr_id):
    admin_id = session.get('admin_id')  # Get admin_id from session set by the decorator
    hr = HR.query.get_or_404(hr_id)
    if not hr:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.home', admin_id=admin_id))
    
    return render_template('admin/view_hr_info.html', hr=hr, admin_id=admin_id)
