import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    load_dotenv()  
    PROPAGATE_EXCEPTIONS = True
    PORT = int(os.getenv('PORT', 5000))
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    API_TITLE = "STORE CHATBOT MVP"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.1.0"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
    OPEN_API_URL_PREFIX = "/" 
    # Handle DATABASE_URL correctly
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url.replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///chat.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') 
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') 
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    from datetime import timedelta
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Set token expiration time
    #JWT_TOKEN_LOCATION = ["cookies"]
    #JWT_COOKIE_SECURE = True  # Enable this for HTTPS only
    #JWT_COOKIE_CSRF_PROTECT = True  # CSRF protection
    #JWT_TOKEN_LOCATION = ["headers"]  # Default to using headers
    #JWT_TOKEN_LOCATION = ["headers"]  # or include "cookies" if you're also using cookies
    #JWT_HEADER_NAME = "Authorization"
    #JWT_HEADER_TYPE = "Bearer"
    # Configure JWT to use cookies
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Set to True if you want CSRF protection on cookies






    