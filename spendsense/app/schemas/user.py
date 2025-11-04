"""
User schema for Pydantic validation.

This defines the structure and validation rules for User data.

Why this exists:
- Validates user data before it enters the database
- Provides clear error messages for invalid data
- Uses masked identifiers (no real PII)
- Ensures data consistency across the application
"""

from datetime import datetime

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
    - POST /users endpoint
    """
    pass


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

