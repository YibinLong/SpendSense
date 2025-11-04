"""
Liability schema for Pydantic validation.

This defines the structure for liabilities (credit cards, loans).

Why this exists:
- Tracks credit card balances and limits for utilization calculations
- Validates liability data for persona assignment
- Supports minimum payment and interest tracking
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LiabilityBase(BaseModel):
    """
    Base liability fields.
    
    Covers credit cards, loans, and other liabilities.
    """

    liability_id: str = Field(
        ...,
        description="Unique liability identifier",
        min_length=1,
        max_length=100
    )
    user_id: str = Field(
        ...,
        description="Reference to the user who owns this liability",
        min_length=1
    )
    account_id: str | None = Field(
        default=None,
        description="Related account_id if this liability is linked to an account"
    )
    liability_type: Literal["credit_card", "student_loan", "mortgage", "auto_loan", "personal_loan", "other"] = Field(
        ...,
        description="Type of liability"
    )
    name: str = Field(
        ...,
        description="Liability name (e.g., 'Chase Sapphire Card')",
        min_length=1,
        max_length=255
    )
    current_balance: Decimal = Field(
        ...,
        description="Current balance owed",
        ge=Decimal("0"),
        decimal_places=2
    )
    credit_limit: Decimal | None = Field(
        default=None,
        description="Credit limit (for credit cards)",
        ge=Decimal("0"),
        decimal_places=2
    )
    minimum_payment: Decimal | None = Field(
        default=None,
        description="Minimum payment due this cycle",
        ge=Decimal("0"),
        decimal_places=2
    )
    last_payment_amount: Decimal | None = Field(
        default=None,
        description="Amount of last payment made",
        decimal_places=2
    )
    last_payment_date: date | None = Field(
        default=None,
        description="Date of last payment"
    )
    next_payment_due_date: date | None = Field(
        default=None,
        description="When the next payment is due"
    )
    interest_rate_percentage: Decimal | None = Field(
        default=None,
        description="Annual interest rate as percentage (e.g., 18.99)",
        ge=Decimal("0"),
        le=Decimal("100"),
        decimal_places=2
    )
    is_overdue: bool = Field(
        default=False,
        description="Whether account is overdue"
    )

    @field_validator('current_balance')
    @classmethod
    def validate_current_balance(cls, v: Decimal) -> Decimal:
        """Ensure balance is non-negative."""
        if v < 0:
            raise ValueError("Liability balance cannot be negative")
        return v

    @field_validator('credit_limit')
    @classmethod
    def validate_credit_limit(cls, v: Decimal | None) -> Decimal | None:
        """Ensure credit limit is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("Credit limit cannot be negative")
        return v


class LiabilityCreate(LiabilityBase):
    """
    Schema for creating a new liability.
    
    Used when:
    - Generating synthetic liabilities
    - Ingesting liabilities from CSV/JSON
    """
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this liability record was created"
    )

    @property
    def utilization_percentage(self) -> Decimal | None:
        """
        Calculate credit utilization percentage.
        
        Why this is useful:
        - Core metric for High Utilization persona
        - Returns None if no credit limit (e.g., loans)
        - Returns percentage between 0-100
        
        Example:
            balance = 500, limit = 1000 → 50.0%
        """
        if self.credit_limit and self.credit_limit > 0:
            return (self.current_balance / self.credit_limit) * Decimal("100")
        return None


class Liability(LiabilityBase):
    """
    Complete liability schema with database ID.
    
    Used when:
    - Returning liability data from database
    - Credit utilization calculations
    - Persona assignment (High Utilization persona)
    """

    id: int = Field(..., description="Database primary key")
    created_at: datetime

    model_config = {"from_attributes": True}  # Enables ORM mode for SQLAlchemy compatibility

    @property
    def utilization_percentage(self) -> Decimal | None:
        """
        Calculate credit utilization percentage.
        
        Why this is useful:
        - Core metric for High Utilization persona
        - Returns None if no credit limit (e.g., loans)
        - Returns percentage between 0-100
        
        Example:
            balance = 500, limit = 1000 → 50.0%
        """
        if self.credit_limit and self.credit_limit > 0:
            return (self.current_balance / self.credit_limit) * Decimal("100")
        return None


class LiabilityInDB(Liability):
    """Liability schema as stored in database."""
    pass

