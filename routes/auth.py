"""
Authentication routes for the Lease Clause Classifier API.
Handles login, logout, and session management.
"""

from flask import Blueprint, request, jsonify

from utils import log_success, log_error
from auth import (
    authenticate_user,
    create_session,
    validate_token,
    invalidate_session,
    get_current_user,
    get_user_safe,
    require_auth
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Authenticate user and create session.

    Request JSON:
        {
            "username": "username or email",
            "password": "password"
        }

    Response:
        JSON with token and user info on success.
    """
    try:
        log_success("Login attempt", endpoint="/auth/login")

        data = request.get_json()
        if not data:
            log_error("Login failed - No request body", endpoint="/auth/login")
            return jsonify({"error": "Request body required"}), 400

        username = data.get('username') or data.get('email')
        password = data.get('password')

        if not username or not password:
            log_error("Login failed - Missing credentials", endpoint="/auth/login")
            return jsonify({"error": "Username/email and password are required"}), 400

        # Authenticate user
        user = authenticate_user(username, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        # Create session
        token = create_session(user)

        log_success("Login successful", endpoint="/auth/login", username=user["username"])

        return jsonify({
            "message": "Login successful",
            "token": token,
            "token_type": "Bearer",
            "user": get_user_safe(user)
        }), 200

    except Exception as e:
        log_error("Login failed", endpoint="/auth/login", error=str(e))
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """
    Logout user and invalidate session.

    Headers:
        Authorization: Bearer <token>

    Response:
        JSON with logout status.
    """
    try:
        log_success("Logout attempt", endpoint="/auth/logout")

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            log_error("Logout failed - No authorization header", endpoint="/auth/logout")
            return jsonify({"error": "Authorization header required"}), 401

        # Extract token
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header

        # Invalidate session
        if invalidate_session(token):
            log_success("Logout successful", endpoint="/auth/logout")
            return jsonify({"message": "Logout successful"}), 200
        else:
            log_error("Logout failed - Session not found", endpoint="/auth/logout")
            return jsonify({"error": "Session not found or already expired"}), 404

    except Exception as e:
        log_error("Logout failed", endpoint="/auth/logout", error=str(e))
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user_info():
    """
    Get current authenticated user info.

    Headers:
        Authorization: Bearer <token>

    Response:
        JSON with current user info.
    """
    try:
        log_success("Get current user requested", endpoint="/auth/me")

        user = request.current_user
        if not user:
            return jsonify({"error": "User not found"}), 404

        log_success("Current user retrieved", endpoint="/auth/me", username=user["username"])

        return jsonify({
            "user": get_user_safe(user)
        }), 200

    except Exception as e:
        log_error("Failed to get current user", endpoint="/auth/me", error=str(e))
        return jsonify({"error": str(e)}), 500


@auth_bp.route('/auth/validate', methods=['GET'])
def validate_session():
    """
    Validate a session token.

    Headers:
        Authorization: Bearer <token>

    Response:
        JSON with validation status.
    """
    try:
        log_success("Token validation requested", endpoint="/auth/validate")

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"valid": False, "error": "No authorization header"}), 200

        # Extract token
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header

        # Validate token
        session = validate_token(token)
        if session:
            user = get_current_user(token)
            log_success("Token validated", endpoint="/auth/validate", username=session["username"])
            return jsonify({
                "valid": True,
                "session": {
                    "user_id": session["user_id"],
                    "username": session["username"],
                    "role": session["role"],
                    "expires_at": session["expires_at"]
                },
                "user": get_user_safe(user)
            }), 200
        else:
            log_error("Token validation failed", endpoint="/auth/validate")
            return jsonify({"valid": False, "error": "Invalid or expired token"}), 200

    except Exception as e:
        log_error("Token validation failed", endpoint="/auth/validate", error=str(e))
        return jsonify({"valid": False, "error": str(e)}), 500


@auth_bp.route('/auth/refresh', methods=['POST'])
@require_auth
def refresh_token():
    """
    Refresh session token (get a new token).

    Headers:
        Authorization: Bearer <token>

    Response:
        JSON with new token.
    """
    try:
        log_success("Token refresh requested", endpoint="/auth/refresh")

        # Get current token
        auth_header = request.headers.get('Authorization')
        if auth_header.startswith('Bearer '):
            old_token = auth_header[7:]
        else:
            old_token = auth_header

        user = request.current_user
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Invalidate old session
        invalidate_session(old_token)

        # Create new session
        new_token = create_session(user)

        log_success("Token refreshed", endpoint="/auth/refresh", username=user["username"])

        return jsonify({
            "message": "Token refreshed successfully",
            "token": new_token,
            "token_type": "Bearer",
            "user": get_user_safe(user)
        }), 200

    except Exception as e:
        log_error("Token refresh failed", endpoint="/auth/refresh", error=str(e))
        return jsonify({"error": str(e)}), 500
