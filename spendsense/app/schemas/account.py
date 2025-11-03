"""
Account schema for Pydantic validation.

This defines the structure for bank accounts (checking, savings, credit).

Why this exists:
- Validates account data including holder_category to filter business accounts
- Enforces required fields for financial accounts
- Provides type safety for account types and subtypes
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AccountBase(BaseModel):
    """
    Base account fields.
    
    Matches Plaid-style account structure.
    """
    
    account_id: str = Field(
        ...,
        description="Masked account identifier",
        min_length=1,
        max_length=100
    )
    user_id: str = Field(
        ...,
        description="Reference to the user who owns this account",
        min_length=1
    )
    account_name: str = Field(
        ...,
        description="Human-readable account name (e.g., 'Chase Checking')",
        min_length=1,
        max_length=255
    )
    account_type: Literal["depository", "credit", "loan", "investment"] = Field(
        ...,
        description="High-level account category"
    )
    account_subtype: str = Field(
        ...,
        description="Specific account type (e.g., 'checking', 'savings', 'credit card')",
        max_length=50
    )
    holder_category: Literal["individual", "business", "unknown"] = Field(
        default="individual",
        description="Account holder type - business accounts are filtered out per PRD"
    )
    currency: str = Field(
        default="USD",
        description="Currency code (only USD supported in MVP)",
        max_length=3
    )
    balance_current: Decimal = Field(
        ...,
        description="Current account balance",
        decimal_places=2
    )
    balance_available: Optional[Decimal] = Field(
        default=None,
        description="Available balance (for credit accounts, this is available credit)",
        decimal_places=2
    )
    credit_limit: Optional[Decimal] = Field(
        default=None,
        description="Credit limit for credit accounts",
        decimal_places=2
    )
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Only USD is supported in MVP per PRD."""
        if v.upper() != "USD":
            raise ValueError(f"Unsupported currency: {v}. Only USD is supported in MVP.")
        return v.upper()
    
    @field_validator('holder_category')
    @classmethod
    def validate_holder_category(cls, v: str) -> str:
        """
        Warn if business account (will be filtered per PRD).
        
        Why this matters:
        - PRD specifies filtering out business accounts
        - We validate here but filter during processing
        """
        return v


class AccountCreate(AccountBase):
    """
    Schema for creating a new account.
    
    Used when:
    - Generating synthetic accounts
    - Ingesting accounts from CSV/JSON
    """
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this account was created"
    )


class Account(AccountBase):
    """
    Complete account schema with database ID.
    
    Used when:
    - Returning account data from database
    - API responses
    """
    
    id: int = Field(..., description="Database primary key")
    created_at: datetime
    
    model_config = {"from_attributes": True}  # Enables ORM mode for SQLAlchemy compatibility


class AccountInDB(Account):
    """Account schema as stored in database."""
    pass

