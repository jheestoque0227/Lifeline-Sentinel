from functools import wraps
from flask import abort, redirect, request, url_for
from flask_login import current_user

def role_required(*roles):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login", next=request.full_path))
            if current_user.role not in roles:
                abort(403)
            if not current_user.is_active_user or current_user.deleted_at:
                abort(403)
            return function(*args, **kwargs)
        return wrapper
    return decorator
