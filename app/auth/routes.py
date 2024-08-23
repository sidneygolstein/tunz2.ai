from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, session
from app import db, bcrypt, mail
from datetime import timedelta
from app.models.hr import HR
from app.models.company import Company
from app.models.admin import Admin
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, decode_token, JWTManager
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from helpers import get_url
jwt = JWTManager()
import re


auth = Blueprint('auth', __name__)

# USEFUL METHODS

def generate_confirmation_token(user_id, admin_id):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user_id, 'admin_id': admin_id}, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return user_id

def generate_reset_token(user, user_type, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps({'user_id': user.id, 'user_type': user_type}, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=expiration)
    except:
        return None, None
    if data['user_type'] == 'hr':
        return HR.query.get(data['user_id']), 'hr'
    elif data['user_type'] == 'admin':
        return Admin.query.get(data['user_id']), 'admin'
    return None, None


# Send reset email
def send_reset_email(user, user_type):
    token = generate_reset_token(user, user_type)
    reset_url = get_url('auth.reset_password', token=token)
    
    if user_type == 'admin':
        msg_body = f'''👋 Hello admin, 
        
        You requested to reset your password. Here is the link to reset the password:
        {reset_url}

        If you did not make this request, simply ignore this email.
        '''
    else:
        msg_body = f'''👋 Hello {user.name},
        
        You requested to reset your password. Here is the link to reset the password:
        {reset_url}

        If you did not make this request, simply ignore this email.

        The Tunz.ai team
        '''

    msg = Message('Password Reset Request',
                  sender='noreply@tunz.ai',
                  recipients=[user.email])
    msg.body = msg_body
    mail.send(msg)


def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True



################################################################################################

# ROUTES


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        hr = HR.query.filter_by(email=email).first()

        if hr and hr.check_password(password):
            if hr.confirmed:
                return jsonify({"msg": "✅ Login succeeded", "redirect_url": url_for('main.home', hr_id=hr.id)}), 200
            else:
                return jsonify({"msg": "👋 Hi, the TUNZ admin has not yet approved your registration. Please wait. You will receive an email as soon as you're approved."}), 403
        return jsonify({"msg": "⛔ The email or password you entered is incorrect. Please try again. You can also reset your password if it persists."}), 400
    return render_template('auth/login.html')




# To be enhanced with jwt
@auth.route('/logout', methods=['GET','POST'])
def logout():
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        name = data.get('name')
        surname = data.get('surname')
        company_name = data.get('company_name')

        if password != confirm_password:
            return jsonify({"msg": "⛔ Your 'password' and 'confirm password' do not match, please try again"}), 400
        
        if not is_strong_password(password):
            return jsonify({"msg": "⛔ Password does not meet the criteria: At least 8 characters, one upper case letter, one digit, one special character"}), 400

        existing_user = HR.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"msg": "🤗 It seems that you are already registered. Please login"}), 400
        
        existing_company = Company.query.filter_by(name=company_name).first()
        if not existing_company:
            company = Company(name=company_name)
            db.session.add(company)
            db.session.commit()
        else:
            company = existing_company

        hr = HR(email=email, name=name, surname=surname, company_id=company.id)
        hr.set_password(password)
        hr.confirmed = False  # New accounts need to be confirmed
        db.session.add(hr)
        db.session.commit()

        # Generate confirmation link
        admin = Admin.query.filter_by(email='sidney@tunz.ai').first()
        admin_id = admin.id  # Ensure the admin is logged in when registering a new HR
        admin_email = admin.email #'sidney@tunz.ai'  # Admin email

        if not admin_id:
            return jsonify({"msg": "Admin must be logged in to register a new HR"}), 403
        #confirm_url = url_for('admin.confirm_account', hr_id=hr.id, admin_id=admin_id, _external=True)
        dashboard_url = get_url('admin.home', admin_id=admin_id)
        
        
        # Send confirmation email to admin        
        msg = Message('New Account Registration',
                      sender='noreply@tunz.ai',
                      recipients=[admin_email])
        msg.body = f'New account registration request:\n\nEmail: {email}\nName: {name}\nSurname: {surname}\nCompany: {company_name}\n\nPlease review the account by visiting the following link: {dashboard_url}'
        mail.send(msg)

        return jsonify({"msg": "✅ Your registration request has been sent to the admin for confirmation. You will receive an email as soon as your account is confirmed"}), 200
    return render_template('auth/register.html')







@auth.route('/request_reset_password', methods=['GET', 'POST'])
def request_reset_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        user = None
        user_type = None

        # Check if the email belongs to an admin
        if email == 'sidney@tunz.ai':
            user = Admin.query.filter_by(email=email).first()
            user_type = 'admin'
        
        # If not an admin, check if it's an HR
        if not user:
            user = HR.query.filter_by(email=email).first()
            user_type = 'hr'
        
        if user:
            send_reset_email(user, user_type)
            return jsonify({"msg": "✅ Your password reset request is confirmed. A link was sent to your email. Please check your emails."}), 200
        else:
            return jsonify({"msg": "⛔ We did not find your email. Please try again."}), 404
    
    return render_template('auth/request_reset_password.html')



# Reset password
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user, user_type = verify_reset_token(token)
    if not user:
        return jsonify({"msg": "⛔ Invalid or expired token. Please make a new password request."}), 400
    
    if request.method == 'POST':
        data = request.get_json()
        password = data.get('password')
        password_confirm = data.get('password_confirm')

        if password == password_confirm:
            if not is_strong_password(password):
                return jsonify({"msg": "⛔ Your password does not meet the criteria: At least 8 characters, one upper case letter, one digit, one special character"}), 400
            user.set_password(password)
            db.session.commit()

            if user_type == 'admin':
                return jsonify({"msg": "✅ Admin password reset confirmed. You can now log in.", "redirect_url": url_for('auth.admin_login')}), 200
            else:
                return jsonify({"msg": "✅ Your password has just been reset. You can now log in.", "redirect_url": url_for('auth.login')}), 200
        else:
            return jsonify({"msg": "⛔ Your 'password' and 'confirm password' do not match. Please try again."}), 400
    
    return render_template('auth/reset_password.html', token=token)



## ADMIN AUTH ##

@auth.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        name = data.get('name')
        surname = data.get('surname')

        print('Received data:', data)

        if password != confirm_password:
            return jsonify({"msg": "⛔ Passwords do not match"}), 400
        
        if not is_strong_password(password):
            return jsonify({"msg": "⛔ Password does not meet the criteria: At least 8 characters, one upper case letter, one digit, one special character"}), 400

        if email != 'sidney@tunz.ai':
            return jsonify({"msg": "⛔ Only the designated admin can register"}), 400

        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            return jsonify({"msg": "⛔ Admin already exists"}), 400

        admin = Admin(email=email, name=name, surname=surname)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        return jsonify({"msg": "✅ Admin registration successful"}), 200
    return render_template('auth/admin_register.html')





@auth.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.query.filter_by(email=email).first()

        if admin and admin.check_password(password):
            session['admin_id'] = admin.id  # Store admin_id in session
            session['admin_email'] = admin.email
            return redirect(url_for('admin.home'))
        else:
            return jsonify({"msg": "Invalid credentials"}), 401
    return render_template('auth/admin_login.html')


# To be enhanced with jwt
@auth.route('/admin_logout', methods=['GET','POST'])
def admin_logout():
    return redirect(url_for('auth.admin_login'))