from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
    """Generate an error response with the specified status code and message"""
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(message):
    """400 Bad Request error"""
    return error_response(400, message)

def unauthorized(message="Authentication required"):
    """401 Unauthorized error"""
    return error_response(401, message)

def forbidden(message="You don't have permission to access this resource"):
    """403 Forbidden error"""
    return error_response(403, message)

def not_found(message="Resource not found"):
    """404 Not Found error"""
    return error_response(404, message) 