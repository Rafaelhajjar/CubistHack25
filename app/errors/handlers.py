from flask import render_template, request, jsonify
from app import db
from app.errors import bp

# API error handlers
def wants_json_response():
    """Check if the request wants a JSON response"""
    return request.accept_mimetypes.accept_json and \
        not request.accept_mimetypes.accept_html

@bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if wants_json_response():
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    if wants_json_response():
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if wants_json_response():
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403

@bp.app_errorhandler(401)
def unauthorized_error(error):
    """Handle 401 errors"""
    if wants_json_response():
        return jsonify({'error': 'Unauthorized'}), 401
    return render_template('errors/401.html'), 401 