"""
Consent event schema for Pydantic validation.

This tracks user consent for data processing.

Why this exists:
- Users must explicitly opt into data processing (PRD requirement)
- Consent can be revoked at any time
- Full audit trail of consent changes
- Supports consent guardrails and 403 blocking
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConsentEventBase(BaseModel):
    """
    Base consent event fields.
    
    Tracks every consent action (opt-in, opt-out) with full context.
    """

    user_id: str = Field(
        ...,
        description="User who gave or revoked consent",
        min_length=1
    )
    action: Literal["opt_in", "opt_out"] = Field(
        ...,
        description="Whether user opted in or out of data processing"
    )
    reason: str | None = Field(
        default=None,
        description="Optional reason for consent action",
        max_length=500
    )
    consent_given_by: str = Field(
        ...,
        description="How consent was given (e.g., 'user_dashboard', 'api', 'operator')",
        max_length=100
    )


class ConsentEventCreate(ConsentEventBase):
    """
    Schema for creating a new consent event.
    
    Used when:
    - POST /consent endpoint
    - User opts in/out via dashboard
    - Operator manages consent
    """
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this consent action occurred"
    )


class ConsentEvent(ConsentEventBase):
    """
    Complete consent event schema with database ID.
    
    Used when:
    - Checking current consent status
    - Showing consent history
    - Auditing consent changes
    """

    id: int = Field(..., description="Database primary key")
    timestamp: datetime

    model_config = {"from_attributes": True}  # Enables ORM mode for SQLAlchemy compatibility


class ConsentEventInDB(ConsentEvent):
    """Consent event schema as stored in database."""
    pass


class ConsentStatus(BaseModel):
    """
    Current consent status for a user.
    
    Why this is separate:
    - Provides a simple yes/no answer for "does user have consent?"
    - Derived from most recent ConsentEvent
    - Used by consent guardrails to block processing
    
    Used when:
    - Checking if processing is allowed before any operation
    - Returning 403 with guidance when consent missing
    """

    user_id: str
    has_consent: bool = Field(
        ...,
        description="Whether user currently has active consent"
    )
    last_action: Literal["opt_in", "opt_out"] | None = Field(
        default=None,
        description="Most recent consent action"
    )
    last_updated: datetime | None = Field(
        default=None,
        description="When consent was last changed"
    )

