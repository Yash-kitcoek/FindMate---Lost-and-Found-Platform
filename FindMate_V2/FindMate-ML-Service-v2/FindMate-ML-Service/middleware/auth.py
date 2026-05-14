"""
API Key Authentication Middleware
"""

from flask import request, jsonify
from functools import wraps
import os

def require_api_key(f):
    """
    Decorator to require API key authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('ML_SERVICE_API_KEY')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        if api_key != expected_key:
            return jsonify({'error': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
