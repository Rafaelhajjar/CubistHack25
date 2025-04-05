from flask import jsonify, request, url_for, g, abort
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app import db
from app.api import bp
from app.models.user import User
from app.api.errors import error_response
from datetime import datetime, timedelta
import secrets

# Basic auth for username/password
basic_auth = HTTPBasicAuth()
# Token auth for API access
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username, password):
    """Verify username and password"""
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        return user
    return None

@basic_auth.error_handler
def basic_auth_error(status):
    """Handle basic auth errors"""
    return error_response(status)

@token_auth.verify_token
def verify_token(token):
    """Verify authentication token"""
    from app.models.token import Token
    token_obj = Token.query.filter_by(token=token).first()
    if token_obj and not token_obj.is_expired():
        # Update last used time
        token_obj.last_used = datetime.utcnow()
        db.session.commit()
        return token_obj.user
    return None

@token_auth.error_handler
def token_auth_error(status):
    """Handle token auth errors"""
    return error_response(status)

@bp.route('/auth/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    """Generate authentication token"""
    from app.models.token import Token
    
    # Get or create token
    token = Token.query.filter_by(user_id=basic_auth.current_user().id).first()
    
    if not token:
        token = Token(
            user_id=basic_auth.current_user().id,
            token=secrets.token_hex(32),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(token)
    elif token.is_expired():
        # Regenerate expired token
        token.token = secrets.token_hex(32)
        token.expires_at = datetime.utcnow() + timedelta(days=30)
    
    token.last_used = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'token': token.token,
        'expires_at': token.expires_at.isoformat(),
        'user_id': token.user_id
    })

@bp.route('/auth/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    """Revoke the current token"""
    from app.models.token import Token
    token = Token.query.filter_by(user_id=g.current_user.id).first()
    
    if token:
        db.session.delete(token)
        db.session.commit()
    
    return '', 204

@bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json() or {}
    
    # Check required fields
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return error_response(400, 'Must include username, email, and password fields')
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return error_response(400, 'Please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return error_response(400, 'Please use a different email address')
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', '')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Return the new user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    }), 201, {'Location': url_for('api.get_user', id=user.id)}

@bp.route('/auth/profile', methods=['GET'])
@token_auth.login_required
def get_profile():
    """Get the current user's profile"""
    user = g.current_user
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_admin': user.is_admin,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'created_at': user.created_at.isoformat()
    }) 