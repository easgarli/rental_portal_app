from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask import session, request, abort
from functools import wraps

csrf = CSRFProtect()

def check_csrf():
    """Custom CSRF check for AJAX requests"""
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        token = request.headers.get('X-CSRFToken')
        if not token:
            abort(400, 'CSRF token missing')

def csrf_exempt(view_function):
    """Decorator to exempt a view from CSRF protection"""
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        return view_function(*args, **kwargs)
    return wrapped

def init_csrf(app):
    csrf.init_app(app)
    
    # Add CSRF token to all responses
    @app.after_request
    def add_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            token = generate_csrf()
            response.set_cookie('csrf_token', token)
        return response
    
    # Add CSRF token to template context
    @app.context_processor
    def csrf_context_processor():
        return {
            'csrf_token': generate_csrf(),
            'csrf_token_header': 'X-CSRFToken'
        } 