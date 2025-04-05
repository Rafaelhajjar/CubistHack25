import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
mail = Mail()
cors = CORS()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    cors.init_app(app)
    
    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register error handlers
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # Initialize Dash apps
    with app.app_context():
        from app.dashboards.main_dashboard import init_dashboard
        app = init_dashboard(app)
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app.models import user, congestion_data 