# This file initializes the Flask application and SQLAlchemy.


from flask import Flask, session 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask import Flask, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail, Message
from markupsafe import Markup
from flask import jsonify, redirect, url_for, flash, make_response


db = SQLAlchemy(session_options={"autoflush": False})
jwt = JWTManager()
# Customize what happens when a user is not authorized


migrate = Migrate()
mail = Mail()
bcrypt = Bcrypt()



def create_app():
    app = Flask(__name__,static_folder='static')
    app.config.from_object(Config)
    # Initialize Flask-Session
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    @app.template_filter('nl2br')
    def nl2br(value):
        return Markup(value.replace('\n', '<br>\n'))

    with app.app_context():
        from app import models
        from .main.routes import main as main_blueprint
        from .auth.routes import auth as auth_blueprint
        from .api.routes import api as api_blueprint
        from .admin.routes import admin as admin_blueprint
        app.register_blueprint(main_blueprint)          # we import the main blueprint and register it with the Flask application.
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        app.register_blueprint(api_blueprint, url_prefix='/api')
        app.register_blueprint(admin_blueprint, url_prefix='/admin')


        # Import models
        from .models import answer, applicant, company, hr, interview_parameter, interview, question, result, session, review, review_question, admin, RevokedToken
        # Token revocation check
        @jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            jti = jwt_payload["jti"]
            return RevokedToken.is_jti_blacklisted(jti)
        
        # Handle missing token
        @jwt.unauthorized_loader
        def unauthorized_loader_callback(error):
            # Redirect to login page with an alert message
            response = make_response(redirect(url_for('auth.login')))
            flash('⛔ Your are not authorized to access this page. Please log in again.', 'error')
            return response

        # Handle expired token
        @jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            response = make_response(redirect(url_for('auth.login')))
            flash('⛔ Your session has expired. Please log in again.', 'error')
            return response

        # Handle invalid token
        @jwt.invalid_token_loader
        def invalid_token_callback(error):
            response = make_response(redirect(url_for('auth.login')))
            flash('⛔ Your token is invalid. Please log in again.', 'error')
            return response

        # Handle revoked token
        @jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            response = make_response(redirect(url_for('auth.login')))
            flash('⛔ Your session has been revoked. Please log in again.', 'error')
            return response
    return app

