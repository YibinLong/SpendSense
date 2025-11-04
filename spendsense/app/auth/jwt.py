"""
JWT token creation and validation.

This module handles JSON Web Tokens for stateless authentication.

Why this exists:
- JWTs enable stateless authentication (no server-side session storage)
- Tokens contain user identity and role for authorization
- Signed with secret key to prevent tampering
- Expiration built-in for security

How it works:
- create_access_token(): Encodes user data into signed JWT
- decode_access_token(): Validates and decodes JWT back to user data
- Uses python-jose for JWT operations
"""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from spendsense.app.core.config import settings


class InvalidTokenError(Exception):
    """
    Raised when JWT token is invalid or malformed.
    
    Why we have this:
    - Provides specific error type for invalid tokens
    - Used to return 401 Unauthorized in API
    - Distinguishes from other JWT errors
    """
    pass


class ExpiredTokenError(Exception):
    """
    Raised when JWT token has expired.
    
    Why we have this:
    - Provides specific error type for expired tokens
    - Used to return 401 Unauthorized in API
    - Helpful for client to know to re-login
    """
    pass


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    
    This function encodes user data (user_id, role) into a signed JWT token
    that can be used for authentication.
    
    Args:
        data: Dictionary of data to encode (typically user_id and role)
        expires_delta: Optional custom expiration time (default: from settings)
    
    Returns:
        Signed JWT token string
    
    Example:
        >>> token_data = {"user_id": "user_001", "role": "card_user"}
        >>> token = create_access_token(token_data)
        >>> print(token)  # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
    Why we do this:
    - Creates stateless auth token (no server session needed)
    - Token is signed with secret key to prevent tampering
    - Expiration included for security
    - Payload includes identity and role for authorization
    """
    # Make a copy to avoid modifying input
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    # Add expiration to payload
    to_encode.update({"exp": expire})
    
    # Encode and sign the JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    This function verifies the token signature and expiration,
    then returns the decoded payload.
    
    Args:
        token: JWT token string to decode
    
    Returns:
        Dictionary containing decoded token data (user_id, role, exp)
    
    Raises:
        InvalidTokenError: If token is malformed or signature is invalid
        ExpiredTokenError: If token has expired
    
    Example:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_access_token(token)
        >>> print(payload["user_id"])  # "user_001"
    
    Why we do this:
    - Validates token wasn't tampered with (signature check)
    - Ensures token hasn't expired
    - Extracts user identity and role for authorization
    - Raises specific errors for different failure modes
    """
    try:
        # Decode and verify JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    
    except jwt.ExpiredSignatureError:
        # Token has expired - user needs to re-login
        raise ExpiredTokenError("Token has expired")
    
    except JWTError as e:
        # Invalid token (malformed, wrong signature, etc.)
        raise InvalidTokenError(f"Invalid token: {str(e)}")

