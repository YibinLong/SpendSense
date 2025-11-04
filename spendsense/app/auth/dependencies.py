"""
FastAPI authentication dependencies.

This module provides dependency functions for route protection.

Why this exists:
- FastAPI dependencies enable clean, reusable authentication
- Dependencies can be added to routes via Depends()
- Automatic 401/403 error handling
- Type-safe user extraction from tokens

How it works:
- OAuth2 password bearer scheme for token extraction
- get_current_user(): Validates token and returns user from DB
- require_card_user(): Ensures user has card_user role
- require_operator(): Ensures user has operator role
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from spendsense.app.auth.jwt import InvalidTokenError, ExpiredTokenError, decode_access_token
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import User
from spendsense.app.db.session import get_db

logger = get_logger(__name__)

# OAuth2 password bearer scheme
# This tells FastAPI to look for "Authorization: Bearer <token>" header
# and provides automatic API docs with "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",  # URL where clients get tokens
    auto_error=True  # Automatically return 401 if token missing
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Get currently authenticated user from JWT token.
    
    This dependency extracts and validates the JWT token from the
    Authorization header, then loads the user from the database.
    
    Args:
        token: JWT token from Authorization header (injected by oauth2_scheme)
        session: Database session (injected by get_db)
    
    Returns:
        User object from database
    
    Raises:
        HTTPException: 401 if token is invalid/expired or user not found
    
    Example usage in route:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    
    Why we do this:
    - Validates JWT signature and expiration
    - Loads full user object from database
    - Ensures user is active
    - Provides type-safe user object to routes
    """
    # Decode and validate token
    try:
        payload = decode_access_token(token)
    except (InvalidTokenError, ExpiredTokenError) as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token payload
    user_id: str | None = payload.get("user_id")
    if user_id is None:
        logger.warning("Token missing user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Load user from database
    user = session.query(User).filter(User.user_id == user_id).first()
    if user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Authenticated user: {user_id} (role: {user.role})")
    return user


def require_card_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Require authenticated user to have 'card_user' role.
    
    This dependency extends get_current_user to also check the role.
    Use this for endpoints that should only be accessible to card users.
    
    Args:
        current_user: Authenticated user (injected by get_current_user)
    
    Returns:
        User object (same as input)
    
    Raises:
        HTTPException: 403 if user doesn't have card_user role
    
    Example usage:
        @app.get("/dashboard/{user_id}")
        def dashboard(
            user_id: str,
            current_user: User = Depends(require_card_user)
        ):
            # Ensure user can only access their own data
            if current_user.user_id != user_id:
                raise HTTPException(403, "Access denied")
            return {"data": "..."}
    
    Why we do this:
    - Enforces role-based access control
    - Returns 403 Forbidden (not 401) for wrong role
    - Composable with other dependencies
    """
    if current_user.role != "card_user":
        logger.warning(f"Card user access denied for {current_user.user_id} (role: {current_user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: card_user role required"
        )
    
    return current_user


def require_operator(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Require authenticated user to have 'operator' role.
    
    This dependency extends get_current_user to check for operator role.
    Use this for admin/operator-only endpoints.
    
    Args:
        current_user: Authenticated user (injected by get_current_user)
    
    Returns:
        User object (same as input)
    
    Raises:
        HTTPException: 403 if user doesn't have operator role
    
    Example usage:
        @app.get("/operator/review")
        def operator_review(
            current_user: User = Depends(require_operator)
        ):
            # Only operators can access this
            return {"reviews": "..."}
    
    Why we do this:
    - Protects operator-only endpoints
    - Clear error message for insufficient permissions
    - Type-safe operator user object
    """
    if current_user.role != "operator":
        logger.warning(f"Operator access denied for {current_user.user_id} (role: {current_user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: operator role required"
        )
    
    return current_user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_db)
) -> User | None:
    """
    Get current user if authenticated, otherwise return None.
    
    This dependency is useful for endpoints that have different behavior
    for authenticated vs anonymous users, but don't require authentication.
    
    Args:
        token: Optional JWT token from Authorization header
        session: Database session
    
    Returns:
        User object if authenticated, None otherwise
    
    Example usage:
        @app.get("/content")
        def get_content(current_user: User | None = Depends(get_optional_user)):
            if current_user:
                return {"content": "personalized", "user": current_user.user_id}
            return {"content": "generic"}
    
    Why we do this:
    - Enables optional authentication
    - No 401 error if token missing
    - Clean pattern for public endpoints with optional personalization
    """
    if token is None:
        return None
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if user_id:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user and user.is_active:
                return user
    except (InvalidTokenError, ExpiredTokenError):
        # Silently fail for optional auth
        pass
    
    return None

