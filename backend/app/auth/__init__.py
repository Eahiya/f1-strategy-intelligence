"""
F1 Strategy Intelligence System - Security Layer v3.1
Authentication and Authorization Module

Provides JWT-based authentication, RBAC, and security utilities.
"""
from .dependencies import (
    get_current_user,
    require_admin,
    require_engineer,
    require_viewer,
    check_permissions
)
from .auth_handler import AuthHandler
from .models import User, UserRole

__all__ = [
    'get_current_user',
    'require_admin',
    'require_engineer',
    'require_viewer',
    'check_permissions',
    'AuthHandler',
    'User',
    'UserRole'
]
