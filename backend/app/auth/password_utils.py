"""
Password hashing and verification utilities.
Uses bcrypt for secure password handling.
"""
from passlib.context import CryptContext

# Configure bcrypt password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor - higher = more secure but slower
)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def check_password_strength(password: str) -> tuple[bool, str]:
    """
    Check if password meets security requirements.
    
    Args:
        password: Password to check
        
    Returns:
        (is_valid, message) tuple
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


if __name__ == "__main__":
    # Test password utilities
    print("Testing Password Utilities")
    print("=" * 50)
    
    test_passwords = [
        "weak",
        "password123",
        "Password123",
        "Password123!"
    ]
    
    for pwd in test_passwords:
        is_strong, msg = check_password_strength(pwd)
        status = "✓" if is_strong else "✗"
        print(f"{status} '{pwd}': {msg}")
    
    # Test hashing
    print("\nTesting Hashing:")
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed[:30]}...")
    
    # Verify correct password
    is_valid = verify_password(password, hashed)
    print(f"✓ Correct password verifies: {is_valid}")
    
    # Verify wrong password
    is_valid = verify_password("WrongPass", hashed)
    print(f"✗ Wrong password rejected: {not is_valid}")
    
    print("\n✓ Password utilities working correctly!")
