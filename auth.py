"""
Authentication module for the Lease Clause Classifier API.
Contains user data, authentication functions, and token management.
Uses MongoDB users collection with fallback to sample users.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import request, jsonify, current_app

from utils import log_success, log_error

# Sample users data (fallback when MongoDB users collection is not available)
SAMPLE_USERS = [
    {
        "id": "usr_001",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "first_name": "System",
        "last_name": "Administrator",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "last_login": None
    },
    {
        "id": "usr_002",
        "username": "john.doe",
        "email": "john.doe@example.com",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "role": "user",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "created_at": "2024-02-15T10:30:00Z",
        "last_login": "2024-12-20T14:25:00Z"
    },
    {
        "id": "usr_003",
        "username": "jane.smith",
        "email": "jane.smith@example.com",
        "password_hash": hashlib.sha256("password456".encode()).hexdigest(),
        "role": "user",
        "first_name": "Jane",
        "last_name": "Smith",
        "is_active": True,
        "created_at": "2024-03-10T08:15:00Z",
        "last_login": "2024-12-22T09:45:00Z"
    },
    {
        "id": "usr_004",
        "username": "bob.wilson",
        "email": "bob.wilson@example.com",
        "password_hash": hashlib.sha256("securepass".encode()).hexdigest(),
        "role": "editor",
        "first_name": "Bob",
        "last_name": "Wilson",
        "is_active": True,
        "created_at": "2024-04-20T16:00:00Z",
        "last_login": "2024-12-18T11:30:00Z"
    },
    {
        "id": "usr_005",
        "username": "alice.johnson",
        "email": "alice.johnson@example.com",
        "password_hash": hashlib.sha256("alicepass".encode()).hexdigest(),
        "role": "viewer",
        "first_name": "Alice",
        "last_name": "Johnson",
        "is_active": False,
        "created_at": "2024-05-05T12:00:00Z",
        "last_login": "2024-10-15T08:00:00Z"
    }
]

# Active sessions (token -> user_id mapping)
active_sessions = {}

# Token expiry duration (in hours)
TOKEN_EXPIRY_HOURS = 24

# Users collection name
USERS_COLLECTION = "users"

# Cache for checking if MongoDB users exist
_use_mongodb_users = None


def get_users_collection():
    """
    Get MongoDB users collection if available.

    Returns:
        Tuple of (collection, client) or (None, None) if not available.
    """
    try:
        from db import get_mongo_config
        import os

        # Try to get config from Flask app context
        try:
            config = current_app.config.get('APP_CONFIG', {})
        except RuntimeError:
            # Outside of app context, try to load config manually
            config = {}

        mongo_config = config.get("mongodb", {})
        mongo_uri = os.environ.get('MONGODB_URI') or mongo_config.get("uri", "")
        mongo_db = mongo_config.get("database", "")

        if not mongo_uri or not mongo_db:
            return None, None

        from pymongo import MongoClient
        client = MongoClient(mongo_uri)
        db = client[mongo_db]
        collection = db[USERS_COLLECTION]

        return collection, client

    except Exception as e:
        log_error("Failed to get users collection", error=str(e))
        return None, None


def check_mongodb_users_exist():
    """
    Check if MongoDB users collection exists and has data.

    Returns:
        True if MongoDB users collection has data, False otherwise.
    """
    global _use_mongodb_users

    # Return cached result if available
    if _use_mongodb_users is not None:
        return _use_mongodb_users

    try:
        collection, client = get_users_collection()
        if collection is None:
            _use_mongodb_users = False
            return False

        # Check if users collection has any documents
        count = collection.count_documents({}, limit=1)
        client.close()

        _use_mongodb_users = count > 0

        if _use_mongodb_users:
            log_success("Using MongoDB users collection")
        else:
            log_success("Using sample users (MongoDB users collection is empty)")

        return _use_mongodb_users

    except Exception as e:
        log_error("Error checking MongoDB users", error=str(e))
        _use_mongodb_users = False
        return False


def reset_users_cache():
    """Reset the MongoDB users cache to force re-checking."""
    global _use_mongodb_users
    _use_mongodb_users = None


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token():
    """Generate a secure random token."""
    return secrets.token_hex(32)


def serialize_user(user):
    """
    Serialize a user document for consistent format.
    Handles both MongoDB documents and sample user dicts.
    """
    if not user:
        return None

    # Handle MongoDB ObjectId
    user_id = user.get("id") or user.get("_id")
    if hasattr(user_id, '__str__') and not isinstance(user_id, str):
        user_id = str(user_id)

    return {
        "id": user_id,
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "password_hash": user.get("password_hash", ""),
        "role": user.get("role", "user"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", ""),
        "last_login": user.get("last_login")
    }


def find_user_by_username(username):
    """Find a user by username."""
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                user = collection.find_one({"username": username})
                client.close()
                if user:
                    return serialize_user(user)
        except Exception as e:
            log_error("Error finding user by username in MongoDB", error=str(e))

    # Fallback to sample users
    for user in SAMPLE_USERS:
        if user["username"] == username:
            return user
    return None


def find_user_by_email(email):
    """Find a user by email."""
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                user = collection.find_one({"email": email})
                client.close()
                if user:
                    return serialize_user(user)
        except Exception as e:
            log_error("Error finding user by email in MongoDB", error=str(e))

    # Fallback to sample users
    for user in SAMPLE_USERS:
        if user["email"] == email:
            return user
    return None


def find_user_by_id(user_id):
    """Find a user by ID."""
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                from bson import ObjectId

                # Try finding by _id (ObjectId) first
                try:
                    user = collection.find_one({"_id": ObjectId(user_id)})
                except Exception:
                    user = None

                # Try finding by id field
                if not user:
                    user = collection.find_one({"id": user_id})

                # Try finding by _id as string
                if not user:
                    user = collection.find_one({"_id": user_id})

                client.close()
                if user:
                    return serialize_user(user)
        except Exception as e:
            log_error("Error finding user by ID in MongoDB", error=str(e))

    # Fallback to sample users
    for user in SAMPLE_USERS:
        if user["id"] == user_id:
            return user
    return None


def get_all_users():
    """
    Get all users from MongoDB or sample data.

    Returns:
        List of user dicts.
    """
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                users = list(collection.find({}))
                client.close()
                return [serialize_user(user) for user in users]
        except Exception as e:
            log_error("Error getting all users from MongoDB", error=str(e))

    # Fallback to sample users
    return SAMPLE_USERS.copy()


def create_user_in_db(user_data):
    """
    Create a new user in MongoDB.

    Args:
        user_data: User data dict.

    Returns:
        Created user dict or None if failed.
    """
    try:
        collection, client = get_users_collection()
        if collection is None:
            # Fall back to adding to SAMPLE_USERS
            SAMPLE_USERS.append(user_data)
            log_success("User added to sample users", username=user_data.get("username"))
            return user_data

        # Add created_at timestamp
        user_data["created_at"] = datetime.utcnow().isoformat() + "Z"

        result = collection.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)

        # Reset cache since we added a user
        reset_users_cache()

        client.close()
        log_success("User created in MongoDB", username=user_data.get("username"))
        return serialize_user(user_data)

    except Exception as e:
        log_error("Error creating user in MongoDB", error=str(e))
        # Fall back to adding to SAMPLE_USERS
        SAMPLE_USERS.append(user_data)
        return user_data


def update_user_in_db(user_id, update_data):
    """
    Update a user in MongoDB.

    Args:
        user_id: User ID.
        update_data: Dict of fields to update.

    Returns:
        True if successful, False otherwise.
    """
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                from bson import ObjectId

                # Try updating by _id (ObjectId)
                try:
                    result = collection.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": update_data}
                    )
                    if result.modified_count > 0 or result.matched_count > 0:
                        client.close()
                        return True
                except Exception:
                    pass

                # Try updating by id field
                result = collection.update_one(
                    {"id": user_id},
                    {"$set": update_data}
                )
                client.close()
                return result.modified_count > 0 or result.matched_count > 0

        except Exception as e:
            log_error("Error updating user in MongoDB", error=str(e))

    # Fallback to sample users
    for user in SAMPLE_USERS:
        if user["id"] == user_id:
            user.update(update_data)
            return True
    return False


def delete_user_from_db(user_id):
    """
    Delete a user from MongoDB.

    Args:
        user_id: User ID.

    Returns:
        True if successful, False otherwise.
    """
    if check_mongodb_users_exist():
        try:
            collection, client = get_users_collection()
            if collection is not None:
                from bson import ObjectId

                # Try deleting by _id (ObjectId)
                try:
                    result = collection.delete_one({"_id": ObjectId(user_id)})
                    if result.deleted_count > 0:
                        client.close()
                        reset_users_cache()
                        return True
                except Exception:
                    pass

                # Try deleting by id field
                result = collection.delete_one({"id": user_id})
                client.close()

                if result.deleted_count > 0:
                    reset_users_cache()
                    return True

        except Exception as e:
            log_error("Error deleting user from MongoDB", error=str(e))

    # Fallback to sample users
    for i, user in enumerate(SAMPLE_USERS):
        if user["id"] == user_id:
            SAMPLE_USERS.pop(i)
            return True
    return False


def authenticate_user(username_or_email, password):
    """
    Authenticate a user by username/email and password.

    Args:
        username_or_email: Username or email address.
        password: Plain text password.

    Returns:
        User dict if authentication successful, None otherwise.
    """
    # Try to find user by username first, then email
    user = find_user_by_username(username_or_email)
    if not user:
        user = find_user_by_email(username_or_email)

    if not user:
        log_error("Authentication failed - User not found", username=username_or_email)
        return None

    if not user.get("is_active", True):
        log_error("Authentication failed - User inactive", username=username_or_email)
        return None

    # Verify password
    print("password ", password)
    password_hash = hash_password(password)
    password_hash = password
    if user.get("password_hash") != password_hash:
        log_error("Authentication failed - Invalid password", username=username_or_email)
        return None

    log_success("User authenticated", username=user.get("username"), user_id=user.get("id"))
    return user


def create_session(user):
    """
    Create a new session for a user.

    Args:
        user: User dict.

    Returns:
        Session token.
    """
    token = generate_token()
    expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)

    user_id = user.get("id") or user.get("_id")
    if hasattr(user_id, '__str__') and not isinstance(user_id, str):
        user_id = str(user_id)

    active_sessions[token] = {
        "user_id": user_id,
        "username": user.get("username"),
        "role": user.get("role"),
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expiry.isoformat()
    }

    # Update last login
    update_user_in_db(user_id, {"last_login": datetime.utcnow().isoformat()})

    log_success("Session created", username=user.get("username"), token_prefix=token[:8])
    return token


def validate_token(token):
    """
    Validate a session token.

    Args:
        token: Session token.

    Returns:
        Session dict if valid, None otherwise.
    """
    if not token:
        return None

    session = active_sessions.get(token)
    if not session:
        return None

    # Check expiry
    expiry = datetime.fromisoformat(session["expires_at"])
    if datetime.utcnow() > expiry:
        # Remove expired session
        del active_sessions[token]
        log_error("Session expired", username=session["username"])
        return None

    return session


def invalidate_session(token):
    """
    Invalidate a session (logout).

    Args:
        token: Session token.

    Returns:
        True if session was invalidated, False if not found.
    """
    if token in active_sessions:
        session = active_sessions[token]
        del active_sessions[token]
        log_success("Session invalidated", username=session["username"])
        return True
    return False


def get_current_user(token):
    """
    Get the current user from a token.

    Args:
        token: Session token.

    Returns:
        User dict if valid, None otherwise.
    """
    session = validate_token(token)
    if not session:
        return None

    return find_user_by_id(session["user_id"])


def get_user_safe(user):
    """
    Get user dict without sensitive information.

    Args:
        user: User dict.

    Returns:
        User dict without password_hash.
    """
    if not user:
        return None

    user_id = user.get("id") or user.get("_id")
    if hasattr(user_id, '__str__') and not isinstance(user_id, str):
        user_id = str(user_id)

    return {
        "id": user_id,
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", ""),
        "last_login": user.get("last_login")
    }


def get_all_users_safe():
    """
    Get all users without sensitive information.

    Returns:
        List of user dicts without password_hash.
    """
    users = get_all_users()
    return [get_user_safe(user) for user in users]


def require_auth(f):
    """
    Decorator to require authentication for an endpoint.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "Authorization header required"}), 401

        # Extract token (support "Bearer <token>" format)
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        else:
            token = auth_header

        session = validate_token(token)
        if not session:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Add session to request context
        request.current_session = session
        request.current_user = find_user_by_id(session["user_id"])

        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    """
    Decorator to require specific roles for an endpoint.

    Args:
        *roles: Allowed roles (e.g., "admin", "editor").
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')

            if not auth_header:
                return jsonify({"error": "Authorization header required"}), 401

            # Extract token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = auth_header

            session = validate_token(token)
            if not session:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Check role
            if session["role"] not in roles:
                log_error("Access denied - Insufficient role",
                         username=session["username"],
                         required_roles=roles,
                         user_role=session["role"])
                return jsonify({"error": "Access denied. Insufficient permissions."}), 403

            # Add session to request context
            request.current_session = session
            request.current_user = find_user_by_id(session["user_id"])

            return f(*args, **kwargs)

        return decorated
    return decorator
