"""
FastAPI dependencies for authentication and authorization.
Provides RBAC (Role-Based Access Control) enforcement.
"""
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .models import User, UserRole, get_db
from .auth_handler import AuthHandler

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: Authorization header credentials
        db: Database session
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If not authenticated (401)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = AuthHandler.decode_token(credentials.credentials)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_active != "true":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        User object if admin
        
    Raises:
        HTTPException: If not admin (403)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_engineer(current_user: User = Depends(get_current_user)) -> User:
    """
    Require engineer or admin role.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        User object if engineer or admin
        
    Raises:
        HTTPException: If not authorized (403)
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or admin access required"
        )
    return current_user


def require_viewer(current_user: User = Depends(get_current_user)) -> User:
    """
    Require any authenticated user (viewer, engineer, or admin).
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        User object if authenticated
        
    Raises:
        HTTPException: If not authenticated (401)
    """
    # Any authenticated user can view
    return current_user


def check_permissions(allowed_roles: List[UserRole]):
    """
    Create a dependency that checks if user has one of the allowed roles.
    
    Args:
        allowed_roles: List of roles that can access the endpoint
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(role_names)}"
            )
        return current_user
    return role_checker


class PermissionChecker:
    """
    Class-based permission checker for more complex scenarios.
    """
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user


# Predefined permission checkers
AdminOnly = PermissionChecker([UserRole.ADMIN])
EngineerPlus = PermissionChecker([UserRole.ADMIN, UserRole.ENGINEER])
AllAuthenticated = PermissionChecker([UserRole.ADMIN, UserRole.ENGINEER, UserRole.VIEWER])


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    token_data = AuthHandler.decode_token(credentials.credentials)
    if not token_data:
        return None
    
    user = db.query(User).filter(User.username == token_data.username).first()
    return user if user and user.is_active == "true" else None


def require_user_owner_or_admin(
    target_user_id: int,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require user to be either the owner of the resource or an admin.
    
    Args:
        target_user_id: ID of the user who owns the resource
        current_user: Currently authenticated user
        
    Returns:
        User object if authorized
        
    Raises:
        HTTPException: If not owner or admin (403)
    """
    if current_user.user_id != target_user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources"
        )
    return current_user


# Role hierarchy for permission inheritance
ROLE_HIERARCHY = {
    UserRole.ADMIN: 3,
    UserRole.ENGINEER: 2,
    UserRole.VIEWER: 1
}


def has_minimum_role(user: User, minimum_role: UserRole) -> bool:
    """
    Check if user has at least the minimum required role.
    
    Args:
        user: User to check
        minimum_role: Minimum role required
        
    Returns:
        True if user meets requirement
    """
    return ROLE_HIERARCHY.get(user.role, 0) >= ROLE_HIERARCHY.get(minimum_role, 0)


if __name__ == "__main__":
    # Test dependencies
    print("Testing RBAC Dependencies")
    print("=" * 60)
    
    # Create mock user
    
    class MockUser:
        def __init__(self, user_id, username, role):
            self.user_id = user_id
            self.username = username
            self.role = role
            self.is_active = "true"
    
    admin = MockUser(1, "admin", UserRole.ADMIN)
    engineer = MockUser(2, "engineer", UserRole.ENGINEER)
    viewer = MockUser(3, "viewer", UserRole.VIEWER)
    
    print("\n1. Role Hierarchy Check")
    print(f"✓ Admin level: {ROLE_HIERARCHY[admin.role]}")
    print(f"✓ Engineer level: {ROLE_HIERARCHY[engineer.role]}")
    print(f"✓ Viewer level: {ROLE_HIERARCHY[viewer.role]}")
    
    print("\n2. Minimum Role Check")
    print(f"✓ Admin meets ENGINEER: {has_minimum_role(admin, UserRole.ENGINEER)}")
    print(f"✓ Engineer meets ENGINEER: {has_minimum_role(engineer, UserRole.ENGINEER)}")
    print(f"✓ Viewer meets ENGINEER: {has_minimum_role(viewer, UserRole.ENGINEER)}")
    
    print("\n3. Permission Checkers")
    print(f"✓ AdminOnly allows admin: {admin.role in AdminOnly.allowed_roles}")
    print(f"✓ EngineerPlus allows engineer: {engineer.role in EngineerPlus.allowed_roles}")
    print(f"✓ AllAuthenticated allows viewer: {viewer.role in AllAuthenticated.allowed_roles}")
    
    print("\n✓ RBAC Dependencies configured correctly!")
