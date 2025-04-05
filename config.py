import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration"""
    # Secret key for session signing, etc.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        f"sqlite:///{os.path.join(basedir, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail server settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Administrative email
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    
    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # Redis for cache/queue
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    
    # Dash settings
    DASH_ROUTES_PATHNAME_PREFIX = '/dash/'
    
    # CSV file path
    CSV_FILE_PATH = os.environ.get('CSV_FILE_PATH') or 'MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250404.csv'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # Use in-memory database
    WTF_CSRF_ENABLED = False
    
class ProductionConfig(Config):
    """Production configuration"""
    # Make sure these are set in environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # PostgreSQL is recommended for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 