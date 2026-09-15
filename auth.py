from functools import wraps
from flask import session, flash, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                flash('غير مصرح لك بالدخول', 'danger')
                return redirect(url_for('dashboard'))
            if session['user_role'] not in allowed_roles:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'danger')
                if session['user_role'] == 'user':
                    return redirect(url_for('user_dashboard'))
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator