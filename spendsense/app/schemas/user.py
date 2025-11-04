"""
User schema for Pydantic validation.

This defines the structure and validation rules for User data.

Why this exists:
- Validates user data before it enters the database
- Provides clear error messages for invalid data
- Uses masked identifiers (no real PII)
- Ensures data consistency across the application
- Includes auth and demographic fields for production-ready app
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """
    Base user fields shared across schemas.
    
    Why we separate Base/Create/Response:
    - Base: common fields
    - Create: fields needed when creating a user
    - Response: fields returned from API (may include computed fields)
    """

    user_id: str = Field(
        ...,
        description="Masked user identifier (no real PII)",
        min_length=1,
        max_length=100
    )
    email_masked: str | None = Field(
        default=None,
        description="Masked email like 'u***@example.com'",
        max_length=255
    )
    phone_masked: str | None = Field(
        default=None,
        description="Masked phone like '***-***-1234'",
        max_length=20
    )
    
    # Role and status
    role: Literal["card_user", "operator"] = Field(
        default="card_user",
        description="User role: card_user or operator"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account is active"
    )
    
    # Demographic fields (optional for privacy)
    age_range: str | None = Field(
        default=None,
        description="Age range: 18-24, 25-34, 35-44, 45-54, 55-64, 65+",
        max_length=20
    )
    gender: str | None = Field(
        default=None,
        description="Gender (optional for privacy)",
        max_length=20
    )
    ethnicity: str | None = Field(
        default=None,
        description="Ethnicity (optional for privacy)",
        max_length=50
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this user record was created"
    )

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Ensure user_id is not empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v.strip()


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    
    Used when:
    - Generating synthetic users
    - Ingesting users from CSV/JSON
    - POST /users endpoint (admin/operator only)
    """
    password: str | None = Field(
        default=None,
        description="Plain-text password (will be hashed before storage)",
        min_length=6
    )


class User(UserBase):
    """
    Complete user schema with database ID.
    
    Used when:
    - Returning user data from the database
    - API responses
    - Internal processing
    """

    id: int = Field(..., description="Database primary key")

    model_config = {"from_attributes": True}  # Enables ORM mode for SQLAlchemy compatibility


class UserInDB(User):
    """
    User schema as stored in database.
    
    This is identical to User for now but allows future
    database-specific fields (like hashed tokens) without
    exposing them in API responses.
    """
    pass


# Alias for API responses
UserResponse = User


# ============================================================================
# Authentication Schemas
# ============================================================================

class LoginRequest(BaseModel):
    """
    Schema for login requests.
    
    Why this exists:
    - Validates login credentials
    - Accepts either user_id or email_masked as username
    - Used by POST /auth/login endpoint
    """
    username: str = Field(
        ...,
        description="Username (user_id or email_masked)",
        min_length=1
    )
    password: str = Field(
        ...,
        description="Plain-text password",
        min_length=1
    )


class SignupRequest(BaseModel):
    """
    Schema for signup/registration requests.
    
    Why this exists:
    - Creates new user accounts with authentication
    - Validates password and confirms match
    - Used by POST /auth/signup endpoint
    """
    user_id: str = Field(
        ...,
        description="Unique user identifier",
        min_length=1,
        max_length=100
    )
    email_masked: str | None = Field(
        default=None,
        description="Masked email (optional)",
        max_length=255
    )
    password: str = Field(
        ...,
        description="Password (min 6 characters)",
        min_length=6
    )
    password_confirm: str = Field(
        ...,
        description="Password confirmation (must match password)",
        min_length=6
    )
    
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure password and password_confirm match."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class TokenResponse(BaseModel):
    """
    Schema for JWT token responses.
    
    Why this exists:
    - Returns access token after successful login/signup
    - Includes token type and user info
    - Standardized response format
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    user_id: str = Field(
        ...,
        description="Authenticated user ID"
    )
    role: str = Field(
        ...,
        description="User role (card_user or operator)"
    )


class UserAuth(BaseModel):
    """
    Schema for authenticated user info from token.
    
    Why this exists:
    - Represents decoded JWT token data
    - Used internally by auth dependencies
    - Contains minimal user info for authorization checks
    """
    user_id: str = Field(
        ...,
        description="User ID from token"
    )
    role: str = Field(
        ...,
        description="User role from token"
    )
    exp: int = Field(
        ...,
        description="Token expiration timestamp"
    )

