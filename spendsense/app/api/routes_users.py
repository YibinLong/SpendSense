"""
User management API routes.

This module provides endpoints for creating and managing users.

Endpoints:
- GET /users - List all users (requires operator role)
- POST /users - Create a new user (requires operator role)
- GET /users/{user_id} - Get a specific user

Why auth guards exist:
- Only operators should create/list users (admin function)
- Protects sensitive user data
"""


from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from spendsense.app.auth.dependencies import require_operator
from spendsense.app.auth.password import hash_password
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import User
from spendsense.app.db.session import get_db
from spendsense.app.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    """
    List all users (operator only).
    
    This endpoint returns all users in the system.
    Only operators can list all users for privacy/security.
    
    Why this exists:
    - Frontend needs to populate user selector dropdowns
    - Operator view needs to show all users for review
    
    Auth: Requires operator role
    
    Response:
        [
            {
                "id": 1,
                "user_id": "user_123",
                "email_masked": "user***@example.com",
                "phone_masked": "***-***-1234",
                "created_at": "2025-11-03T10:30:00"
            },
            ...
        ]
    """
    logger.debug("listing_users", operator=current_user.user_id)

    users = db.query(User).order_by(User.created_at.desc()).all()

    logger.info("users_listed", count=len(users), operator=current_user.user_id)

    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """
    Create a new user (operator only).
    
    This endpoint creates a user record in the database.
    Only operators can create users (admin function).
    
    Why this exists:
    - Users must exist before consent, signals, or personas can be created
    - Returns 409 if user_id already exists
    - Returns 201 with user details on success
    - Supports password for authentication if provided
    
    Auth: Requires operator role
    
    Request body:
        {
            "user_id": "user_123",
            "email_masked": "user***@example.com",
            "phone_masked": "***-***-1234",
            "password": "optional_password",
            "role": "card_user"
        }
    
    Response:
        {
            "id": 1,
            "user_id": "user_123",
            "email_masked": "user***@example.com",
            "phone_masked": "***-***-1234",
            "role": "card_user",
            "created_at": "2025-11-03T10:30:00"
        }
    """
    logger.info("creating_user", user_id=user_data.user_id, operator=current_user.user_id)

    # Check if user already exists
    existing_user = db.query(User).filter(User.user_id == user_data.user_id).first()
    if existing_user:
        logger.warning("user_already_exists", user_id=user_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID '{user_data.user_id}' already exists",
        )

    # Hash password if provided
    password_hash = None
    if user_data.password:
        password_hash = hash_password(user_data.password)

    # Create new user
    new_user = User(
        user_id=user_data.user_id,
        email_masked=user_data.email_masked,
        phone_masked=user_data.phone_masked,
        password_hash=password_hash,
        role=user_data.role,
        is_active=user_data.is_active,
        age_range=user_data.age_range,
        gender=user_data.gender,
        ethnicity=user_data.ethnicity,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info("user_created", user_id=new_user.user_id, db_id=new_user.id, role=new_user.role)

    return UserResponse.model_validate(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """
    Get user details by ID.
    
    Returns 404 if user not found.
    
    Note: Currently public for backward compatibility.
    In production, add authentication and ensure users can only access their own data.
    
    Response:
        {
            "id": 1,
            "user_id": "user_123",
            "email_masked": "user***@example.com",
            "created_at": "2025-11-03T10:30:00"
        }
    """
    logger.debug("getting_user", user_id=user_id)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    return UserResponse.model_validate(user)

