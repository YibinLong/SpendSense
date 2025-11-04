"""
Authentication API routes.

This module provides endpoints for user authentication:
- POST /auth/signup - Register new user account
- POST /auth/login - Authenticate and get JWT token  
- POST /auth/logout - Logout (client-side token deletion)
- GET /auth/me - Get current authenticated user info

Why this exists:
- Enables user account creation and login
- Issues JWT tokens for stateless authentication
- Provides user info endpoint for frontend
- Follows REST best practices
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from spendsense.app.auth.dependencies import get_current_user
from spendsense.app.auth.jwt import create_access_token
from spendsense.app.auth.password import hash_password, verify_password
from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import User as UserModel
from spendsense.app.db.session import get_db
from spendsense.app.schemas.user import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    User,
    UserResponse,
)

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(
    request: SignupRequest,
    session: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    """
    Register a new user account.
    
    This endpoint creates a new user with hashed password and returns
    a JWT token for immediate login.
    
    Process:
    1. Validate that user_id doesn't already exist
    2. Hash the password (never store plain text!)
    3. Create user in database with card_user role
    4. Generate JWT token
    5. Return token and user info
    
    Why we do this:
    - Allows users to self-register
    - Passwords are hashed before storage
    - Immediate authentication after signup
    - Default role is card_user for safety
    
    Args:
        request: SignupRequest with user_id, email, password, password_confirm
        session: Database session (injected)
    
    Returns:
        TokenResponse with access_token, token_type, user_id, role
    
    Raises:
        409 Conflict: If user_id already exists
        400 Bad Request: If validation fails
    """
    logger.info(f"Signup attempt: {request.user_id}")
    
    # Check if user already exists
    existing_user = session.query(UserModel).filter(
        UserModel.user_id == request.user_id
    ).first()
    
    if existing_user:
        logger.warning(f"Signup failed: user_id already exists: {request.user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User ID already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create new user
    new_user = UserModel(
        user_id=request.user_id,
        email_masked=request.email_masked,
        password_hash=password_hash,
        role="card_user",  # Default role for self-registration
        is_active=True
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    logger.info(f"User created successfully: {new_user.user_id}")
    
    # Generate access token
    token_data = {
        "user_id": new_user.user_id,
        "role": new_user.role
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.user_id,
        role=new_user.role
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    session: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    
    This endpoint accepts username (user_id or email) and password,
    validates credentials, and returns a JWT token.
    
    Process:
    1. Look up user by username (try user_id first, then email)
    2. Verify password matches stored hash
    3. Generate JWT token with user info
    4. Return token
    
    Why we do this:
    - Authenticates users for API access
    - Issues JWT tokens for stateless auth
    - Supports login by user_id or email
    - Secure password verification
    
    Args:
        request: LoginRequest with username and password
        session: Database session (injected)
    
    Returns:
        TokenResponse with access_token and user info
    
    Raises:
        401 Unauthorized: If credentials are invalid
    """
    logger.info(f"Login attempt: {request.username}")
    
    # Try to find user by user_id first, then by email
    user = session.query(UserModel).filter(
        UserModel.user_id == request.username
    ).first()
    
    if not user:
        # Try email_masked
        user = session.query(UserModel).filter(
            UserModel.email_masked == request.username
        ).first()
    
    # Validate user exists and password is correct
    if not user or not user.password_hash:
        logger.warning(f"Login failed: user not found or no password set: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(request.password, user.password_hash):
        logger.warning(f"Login failed: incorrect password: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: inactive user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"Login successful: {user.user_id} (role: {user.role})")
    
    # Generate access token
    token_data = {
        "user_id": user.user_id,
        "role": user.role
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        role=user.role
    )


@router.post("/login/form", response_model=TokenResponse)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    """
    OAuth2-compatible login endpoint.
    
    This endpoint is compatible with OAuth2 password flow and FastAPI's
    automatic API docs "Authorize" button. It accepts form data instead of JSON.
    
    Why we have this:
    - Enables FastAPI's automatic API docs authentication
    - Compatible with OAuth2 clients
    - Same logic as /login but accepts form data
    
    Args:
        form_data: OAuth2 form data with username and password
        session: Database session
    
    Returns:
        TokenResponse with access token
    """
    # Convert form data to LoginRequest and call main login logic
    request = LoginRequest(
        username=form_data.username,
        password=form_data.password
    )
    return login(request, session)


@router.post("/logout")
def logout() -> dict[str, str]:
    """
    Logout endpoint (client-side token deletion).
    
    Since JWTs are stateless, the server doesn't track tokens.
    Logout is handled by the client deleting the token from storage.
    
    This endpoint exists for API consistency and to provide
    a clear logout action in API documentation.
    
    Why we do this:
    - Provides explicit logout endpoint
    - Instructs client to delete token
    - No server-side state needed for JWT auth
    
    Returns:
        Success message instructing client to delete token
    """
    logger.info("Logout endpoint called")
    
    return {
        "message": "Successfully logged out. Please delete your access token from client storage."
    }


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[UserModel, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current authenticated user information.
    
    This endpoint returns the full user profile for the authenticated user.
    Useful for frontend to display user info and verify authentication.
    
    Why we do this:
    - Frontend can verify token is still valid
    - Get user info without knowing user_id
    - Useful for displaying current user in UI
    
    Args:
        current_user: Authenticated user from JWT token (injected)
    
    Returns:
        UserResponse with full user profile
    """
    logger.debug(f"User info requested: {current_user.user_id}")
    
    return UserResponse.model_validate(current_user)

