"""
Routes module for the Lease Clause Classifier API.
"""

from .health import health_bp
from .classify import classify_bp
from .data import data_bp
from .clauses import clauses_bp
from .fields import fields_bp
from .auth import auth_bp
from .users import users_bp

__all__ = ['health_bp', 'classify_bp', 'data_bp', 'clauses_bp', 'fields_bp', 'auth_bp', 'users_bp']
