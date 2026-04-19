from functools import wraps
from flask import session, redirect, url_for, abort, request, jsonify


def get_current_user():
    from app.models.user import User
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db_get_user(user_id)


def db_get_user(user_id):
    from app.models.user import User
    return User.query.get(user_id)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if get_current_user() is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("web.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("web.login"))
        if not user.is_admin:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Admin access required"}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated
