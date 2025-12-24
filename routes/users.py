"""
User management routes for the Lease Clause Classifier API.
Handles user listing, retrieval, and management.
Uses MongoDB users collection with fallback to sample users.
"""

import uuid
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from utils import log_success, log_error
from auth import (
    get_all_users,
    get_all_users_safe,
    get_user_safe,
    find_user_by_id,
    find_user_by_username,
    find_user_by_email,
    hash_password,
    create_user_in_db,
    update_user_in_db,
    delete_user_from_db,
    require_auth,
    require_role
)

users_bp = Blueprint('users', __name__)


@users_bp.route('/users', methods=['GET'])
@require_auth
def get_users():
    """
    Get list of all users.

    Headers:
        Authorization: Bearer <token>

    Query Parameters:
        - role: Filter by role (admin, user, editor, viewer)
        - is_active: Filter by active status (true/false)
        - limit: Maximum number of users to return (default: 100)
        - skip: Number of users to skip (default: 0)

    Response:
        JSON with list of users.
    """
    try:
        log_success("Get users requested", endpoint="/users")

        # Get filter parameters
        role_filter = request.args.get('role')
        active_filter = request.args.get('is_active')
        limit = min(int(request.args.get('limit', 100)), 1000)
        skip = int(request.args.get('skip', 0))

        # Get all users (safe version)
        users = get_all_users_safe()

        # Apply filters
        if role_filter:
            users = [u for u in users if u.get("role") == role_filter]

        if active_filter is not None:
            is_active = active_filter.lower() == 'true'
            users = [u for u in users if u.get("is_active") == is_active]

        # Get total count before pagination
        total_count = len(users)

        # Apply pagination
        users = users[skip:skip + limit]

        log_success("Users retrieved", endpoint="/users", count=len(users), total=total_count)

        return jsonify({
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "count": len(users),
            "users": users
        }), 200

    except Exception as e:
        log_error("Failed to get users", endpoint="/users", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users/<user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """
    Get a specific user by ID.

    Headers:
        Authorization: Bearer <token>

    Path Parameters:
        - user_id: User ID

    Response:
        JSON with user info.
    """
    try:
        log_success("Get user requested", endpoint=f"/users/{user_id}", user_id=user_id)

        user = find_user_by_id(user_id)
        if not user:
            log_error("User not found", endpoint=f"/users/{user_id}", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        log_success("User retrieved", endpoint=f"/users/{user_id}", username=user.get("username"))

        return jsonify({
            "user": get_user_safe(user)
        }), 200

    except Exception as e:
        log_error("Failed to get user", endpoint=f"/users/{user_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users/search', methods=['GET'])
@require_auth
def search_users():
    """
    Search users by username or email.

    Headers:
        Authorization: Bearer <token>

    Query Parameters:
        - q: Search query (searches username, email, first_name, last_name)
        - limit: Maximum number of users to return (default: 100)

    Response:
        JSON with matching users.
    """
    try:
        log_success("Search users requested", endpoint="/users/search")

        query = request.args.get('q', '').lower()
        limit = min(int(request.args.get('limit', 100)), 1000)

        if not query:
            return jsonify({"error": "Search query 'q' is required"}), 400

        # Get all users and search
        users = get_all_users_safe()
        matching_users = []

        for user in users:
            username = user.get("username", "").lower()
            email = user.get("email", "").lower()
            first_name = user.get("first_name", "").lower()
            last_name = user.get("last_name", "").lower()

            if (query in username or
                query in email or
                query in first_name or
                query in last_name):
                matching_users.append(user)

        # Apply limit
        matching_users = matching_users[:limit]

        log_success("Users search completed", endpoint="/users/search", query=query, count=len(matching_users))

        return jsonify({
            "query": query,
            "count": len(matching_users),
            "users": matching_users
        }), 200

    except Exception as e:
        log_error("Users search failed", endpoint="/users/search", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users', methods=['POST'])
@require_role('admin')
def create_user():
    """
    Create a new user (admin only).

    Headers:
        Authorization: Bearer <token>

    Request JSON:
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "role": "user"
        }

    Response:
        JSON with created user info.
    """
    try:
        log_success("Create user requested", endpoint="/users")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                log_error("Create user failed - Missing field", endpoint="/users", field=field)
                return jsonify({"error": f"Field '{field}' is required"}), 400

        # Check if username already exists
        if find_user_by_username(data['username']):
            log_error("Create user failed - Username exists", endpoint="/users", username=data['username'])
            return jsonify({"error": "Username already exists"}), 400

        # Check if email already exists
        if find_user_by_email(data['email']):
            log_error("Create user failed - Email exists", endpoint="/users", email=data['email'])
            return jsonify({"error": "Email already exists"}), 400

        # Create new user
        new_user = {
            "id": f"usr_{uuid.uuid4().hex[:8]}",
            "username": data['username'],
            "email": data['email'],
            "password_hash": hash_password(data['password']),
            "role": data.get('role', 'user'),
            "first_name": data.get('first_name', ''),
            "last_name": data.get('last_name', ''),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": None
        }

        # Save to database
        created_user = create_user_in_db(new_user)

        log_success("User created", endpoint="/users", username=new_user["username"], user_id=new_user["id"])

        return jsonify({
            "message": "User created successfully",
            "user": get_user_safe(created_user)
        }), 201

    except Exception as e:
        log_error("Failed to create user", endpoint="/users", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users/<user_id>', methods=['PUT'])
@require_role('admin')
def update_user(user_id):
    """
    Update a user (admin only).

    Headers:
        Authorization: Bearer <token>

    Path Parameters:
        - user_id: User ID

    Request JSON:
        {
            "email": "updated@example.com",
            "first_name": "Updated",
            "last_name": "Name",
            "role": "editor",
            "is_active": true
        }

    Response:
        JSON with updated user info.
    """
    try:
        log_success("Update user requested", endpoint=f"/users/{user_id}", user_id=user_id)

        user = find_user_by_id(user_id)
        if not user:
            log_error("User not found", endpoint=f"/users/{user_id}", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Build update dict
        update_data = {}

        if 'email' in data:
            # Check if email already exists for another user
            existing = find_user_by_email(data['email'])
            existing_id = existing.get('id') if existing else None
            if existing and existing_id != user_id:
                return jsonify({"error": "Email already exists"}), 400
            update_data['email'] = data['email']

        if 'first_name' in data:
            update_data['first_name'] = data['first_name']

        if 'last_name' in data:
            update_data['last_name'] = data['last_name']

        if 'role' in data:
            update_data['role'] = data['role']

        if 'is_active' in data:
            update_data['is_active'] = data['is_active']

        if 'password' in data:
            update_data['password_hash'] = hash_password(data['password'])

        # Update in database
        if update_data:
            update_user_in_db(user_id, update_data)

        # Get updated user
        updated_user = find_user_by_id(user_id)

        log_success("User updated", endpoint=f"/users/{user_id}", username=updated_user.get("username"))

        return jsonify({
            "message": "User updated successfully",
            "user": get_user_safe(updated_user)
        }), 200

    except Exception as e:
        log_error("Failed to update user", endpoint=f"/users/{user_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users/<user_id>', methods=['DELETE'])
@require_role('admin')
def delete_user(user_id):
    """
    Delete a user (admin only).

    Headers:
        Authorization: Bearer <token>

    Path Parameters:
        - user_id: User ID

    Response:
        JSON with deletion status.
    """
    try:
        log_success("Delete user requested", endpoint=f"/users/{user_id}", user_id=user_id)

        # Find user first
        user = find_user_by_id(user_id)
        if not user:
            log_error("User not found", endpoint=f"/users/{user_id}", user_id=user_id)
            return jsonify({"error": "User not found"}), 404

        # Prevent deleting the current user
        current_user = request.current_user
        current_user_id = current_user.get('id') if current_user else None
        if current_user_id and current_user_id == user_id:
            log_error("Cannot delete current user", endpoint=f"/users/{user_id}", user_id=user_id)
            return jsonify({"error": "Cannot delete your own account"}), 400

        # Get username before deletion
        username = user.get("username", "unknown")

        # Delete from database
        deleted = delete_user_from_db(user_id)
        if not deleted:
            log_error("Failed to delete user from database", endpoint=f"/users/{user_id}", user_id=user_id)
            return jsonify({"error": "Failed to delete user"}), 500

        log_success("User deleted", endpoint=f"/users/{user_id}", username=username)

        return jsonify({
            "message": "User deleted successfully",
            "deleted_user_id": user_id,
            "deleted_username": username
        }), 200

    except Exception as e:
        log_error("Failed to delete user", endpoint=f"/users/{user_id}", error=str(e))
        return jsonify({"error": str(e)}), 500


@users_bp.route('/users/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """
    Get user statistics.

    Headers:
        Authorization: Bearer <token>

    Response:
        JSON with user statistics.
    """
    try:
        log_success("Get user stats requested", endpoint="/users/stats")

        users = get_all_users()

        # Calculate stats
        total_users = len(users)
        active_users = sum(1 for u in users if u.get("is_active", True))
        inactive_users = total_users - active_users

        # Count by role
        role_counts = {}
        for user in users:
            role = user.get("role", "user")
            role_counts[role] = role_counts.get(role, 0) + 1

        log_success("User stats retrieved", endpoint="/users/stats", total=total_users)

        return jsonify({
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "users_by_role": role_counts
        }), 200

    except Exception as e:
        log_error("Failed to get user stats", endpoint="/users/stats", error=str(e))
        return jsonify({"error": str(e)}), 500
