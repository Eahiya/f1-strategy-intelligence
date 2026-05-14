"""
Authentication API Routes
Handles user registration, login, and profile management.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from .models import (
    User, UserCreate, UserLogin, UserResponse, Token,
    get_db, UserRole
)
from .auth_handler import AuthHandler, get_token_expiry
from .password_utils import get_password_hash, check_password_strength
from .dependencies import get_current_user, require_admin

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme
security = HTTPBearer()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # Max 5 registrations per minute
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)  # Only admins can register users
):
    """
    Register a new user (Admin only).
    
    - **username**: Unique username (3-50 chars)
    - **email**: Valid email address
    - **password**: Secure password (8+ chars, uppercase, lowercase, digit, special)
    - **role**: User role (admin/engineer/viewer)
    """
    # Check if username exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_strong, msg = check_password_strength(user_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {msg}"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active="true"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user.to_dict()


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Max 10 login attempts per minute
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    - **username**: Registered username
    - **password**: User password
    
    Returns access token and user info.
    """
    # Authenticate user
    user = AuthHandler.authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    tokens = AuthHandler.generate_tokens(user)
    
    return Token(
        access_token=tokens["access_token"],
        token_type="bearer",
        expires_in=get_token_expiry(),
        user=user.to_dict()
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    """
    return current_user.to_dict()


@router.put("/me", response_model=UserResponse)
async def update_profile(
    email: str = None,
    current_password: str = None,
    new_password: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    """
    # Update email if provided
    if email:
        # Check if email is taken
        existing = db.query(User).filter(
            User.email == email,
            User.user_id != current_user.user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = email
    
    # Update password if provided
    if current_password and new_password:
        from .password_utils import verify_password
        
        # Verify current password
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        is_strong, msg = check_password_strength(new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"New password too weak: {msg}"
            )
        
        current_user.hashed_password = get_password_hash(new_password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user.to_dict()


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (Admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [user.to_dict() for user in users]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role (Admin only).
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = new_role
    db.commit()
    
    return {"message": f"User {user.username} role updated to {new_role.value}"}


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account (Admin only).
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deactivation
    if user.user_id == current_admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = "false"
    db.commit()
    
    return {"message": f"User {user.username} deactivated"}


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        from jose import jwt
        from .auth_handler import SECRET_KEY, ALGORITHM
        
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or user.is_active != "true":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        tokens = AuthHandler.generate_tokens(user)
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "bearer",
            "expires_in": get_token_expiry()
        }
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.
    """
    from .password_utils import verify_password
    
    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    is_strong, msg = check_password_strength(new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"New password too weak: {msg}"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


if __name__ == "__main__":
    print("Auth Routes Module")
    print("=" * 50)
    print("Available endpoints:")
    print("  POST /auth/register     - Register new user (Admin only)")
    print("  POST /auth/login        - Authenticate and get tokens")
    print("  GET  /auth/me           - Get current user profile")
    print("  PUT  /auth/me           - Update profile")
    print("  GET  /auth/users        - List all users (Admin)")
    print("  PUT  /auth/users/{id}   - Update user role (Admin)")
    print("  POST /auth/refresh      - Refresh access token")
    print("  POST /auth/change-password - Change password")
    print("\n✓ Auth routes module ready!")
