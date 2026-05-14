"""
JWT Authentication Handler
Manages token creation, validation, and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import HTTPException, status

from .models import User, TokenData


# Security configuration
# In production, these should be loaded from environment variables
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthHandler:
    """Handles JWT token operations and user authentication."""
    
    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Payload data to encode
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),  # Issued at
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict) -> str:
        """
        Create JWT refresh token with longer expiry.
        
        Args:
            data: Payload data to encode
            
        Returns:
            Encoded refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            username: str = payload.get("sub")
            role: str = payload.get("role")
            user_id: int = payload.get("user_id")
            
            if username is None:
                return None
            
            return TokenData(username=username, role=role, user_id=user_id)
            
        except JWTError:
            return None
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify token and return payload or raise exception.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dictionary
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != "access":
                raise credentials_exception
            
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            
            return payload
            
        except JWTError:
            raise credentials_exception
    
    @staticmethod
    def authenticate_user(db, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        from .password_utils import verify_password
        
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if user.is_active != "true":
            return None
        
        return user
    
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """
        Generate access and refresh tokens for user.
        
        Args:
            user: Authenticated user
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        token_data = {
            "sub": user.username,
            "role": user.role.value,
            "user_id": user.user_id
        }
        
        access_token = AuthHandler.create_access_token(token_data)
        refresh_token = AuthHandler.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


def get_token_expiry() -> int:
    """Get access token expiry time in seconds."""
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60


if __name__ == "__main__":
    # Test JWT functionality
    print("Testing JWT Authentication Handler")
    print("=" * 60)
    
    # Test token creation
    test_user = {
        "sub": "test_user",
        "role": "engineer",
        "user_id": 1
    }
    
    print("\n1. Token Creation")
    access_token = AuthHandler.create_access_token(test_user)
    print(f"✓ Access token created: {access_token[:50]}...")
    
    refresh_token = AuthHandler.create_refresh_token(test_user)
    print(f"✓ Refresh token created: {refresh_token[:50]}...")
    
    print("\n2. Token Verification")
    payload = AuthHandler.verify_token(access_token)
    print(f"✓ Token verified: user={payload['sub']}, role={payload['role']}")
    
    print("\n3. Token Decoding")
    token_data = AuthHandler.decode_token(access_token)
    print(f"✓ Token decoded: username={token_data.username}, role={token_data.role}")
    
    print("\n4. Token Expiration")
    print(f"✓ Access tokens expire after: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"✓ Refresh tokens expire after: {REFRESH_TOKEN_EXPIRE_DAYS} days")
    
    print("\n✓ JWT Authentication Handler working correctly!")
