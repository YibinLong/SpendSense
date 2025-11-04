"""
Password hashing and verification utilities.

This module uses passlib with bcrypt for secure password storage.

Why this exists:
- Passwords must NEVER be stored in plain text
- Bcrypt is industry standard for password hashing
- Provides automatic salting and configurable work factor
- Secure against timing attacks

How it works:
- hash_password(): Takes plain password, returns bcrypt hash
- verify_password(): Compares plain password with stored hash
- Uses passlib's CryptContext for consistent API

Note: Bcrypt has a 72-byte password limit. Passwords are truncated if longer.
"""

from passlib.context import CryptContext

# Create password context with bcrypt
# Why bcrypt:
# - Industry standard for password hashing
# - Automatic salting
# - Configurable work factor (rounds)
# - Resistant to rainbow table and brute force attacks
# 
# Note: We configure it to handle bcrypt's 72-byte limitation gracefully
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__default_ident="2b"
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    This function should be used before storing any password in the database.
    The output is a bcrypt hash that includes the salt and work factor.
    
    Args:
        plain_password: The user's password in plain text
    
    Returns:
        A bcrypt hash string safe to store in database
    
    Example:
        >>> password = "my_secret_password"
        >>> hashed = hash_password(password)
        >>> print(hashed)  # $2b$12$...
    
    Why we do this:
    - Storing plain passwords is a critical security vulnerability
    - Bcrypt automatically generates a unique salt per password
    - If database is compromised, passwords remain protected
    
    Note: Bcrypt has a 72-byte limit. Longer passwords are truncated.
    """
    # Ensure password is bytes and truncate to 72 bytes if needed
    # This prevents bcrypt errors with very long passwords
    password_bytes = plain_password.encode('utf-8')[:72]
    password_str = password_bytes.decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password_str)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored hash.
    
    This function is used during login to check if the provided password
    matches the stored hash.
    
    Args:
        plain_password: The password to verify
        hashed_password: The stored bcrypt hash from database
    
    Returns:
        True if password matches, False otherwise
    
    Example:
        >>> stored_hash = "$2b$12$..."  # from database
        >>> is_valid = verify_password("user_input", stored_hash)
        >>> if is_valid:
        ...     print("Login successful")
    
    Why we do this:
    - Secure constant-time comparison (prevents timing attacks)
    - Passlib handles hash format parsing automatically
    - Returns boolean for clean API
    """
    return pwd_context.verify(plain_password, hashed_password)

