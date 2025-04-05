from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.main import bp
from app.models.user import User, SavedDashboard

@bp.route('/')
@bp.route('/index')
def index():
    """Home page"""
    return render_template('index.html', title='Home')

@bp.route('/dashboard')
def dashboard():
    """Main dashboard - redirects to Dash app"""
    return redirect(url_for('main.index', _external=True) + current_app.config.get('DASH_ROUTES_PATHNAME_PREFIX', '/dash/'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', title='Profile')

@bp.route('/saved-dashboards')
@login_required
def saved_dashboards():
    """List of user's saved dashboards"""
    dashboards = SavedDashboard.query.filter_by(user_id=current_user.id).all()
    return render_template('saved_dashboards.html', title='Saved Dashboards', dashboards=dashboards) 