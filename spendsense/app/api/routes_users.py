"""
User management API routes.

This module provides endpoints for creating and managing users.

Endpoints:
- GET /users - List all users
- POST /users - Create a new user
- GET /users/{user_id} - Get a specific user
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.session import get_db
from spendsense.app.db.models import User
from spendsense.app.schemas.user import UserCreate, UserResponse


logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """
    List all users.
    
    This endpoint returns all users in the system.
    
    Why this exists:
    - Frontend needs to populate user selector dropdowns
    - Operator view needs to show all users for review
    
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
    logger.debug("listing_users")
    
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    logger.info("users_listed", count=len(users))
    
    return [UserResponse.model_validate(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Create a new user.
    
    This endpoint creates a user record in the database.
    
    Why this exists:
    - Users must exist before consent, signals, or personas can be created
    - Returns 409 if user_id already exists
    - Returns 201 with user details on success
    
    Request body:
        {
            "user_id": "user_123",
            "email_masked": "user***@example.com",
            "phone_masked": "***-***-1234"
        }
    
    Response:
        {
            "id": 1,
            "user_id": "user_123",
            "email_masked": "user***@example.com",
            "phone_masked": "***-***-1234",
            "created_at": "2025-11-03T10:30:00"
        }
    """
    logger.info("creating_user", user_id=user_data.user_id)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.user_id == user_data.user_id).first()
    if existing_user:
        logger.warning("user_already_exists", user_id=user_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with ID '{user_data.user_id}' already exists",
        )
    
    # Create new user
    new_user = User(
        user_id=user_data.user_id,
        email_masked=user_data.email_masked,
        phone_masked=user_data.phone_masked,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info("user_created", user_id=new_user.user_id, db_id=new_user.id)
    
    return UserResponse.model_validate(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get user details by ID.
    
    Returns 404 if user not found.
    
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

