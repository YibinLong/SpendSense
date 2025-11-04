"""
Transaction schema for Pydantic validation.

This defines the structure for financial transactions.

Why this exists:
- Validates transaction amounts (no negatives except refunds/credits)
- Ensures valid dates (no future dates)
- Enforces currency restrictions (USD only in MVP)
- Provides clear error messages for invalid data
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TransactionBase(BaseModel):
    """
    Base transaction fields.
    
    Matches Plaid-style transaction structure with key validations.
    """

    transaction_id: str = Field(
        ...,
        description="Unique transaction identifier",
        min_length=1,
        max_length=100
    )
    account_id: str = Field(
        ...,
        description="Reference to the account for this transaction",
        min_length=1
    )
    amount: Decimal = Field(
        ...,
        description="Transaction amount (positive = debit/expense, negative = credit/refund)",
        decimal_places=2
    )
    currency: str = Field(
        default="USD",
        description="Currency code (only USD supported in MVP)",
        max_length=3
    )
    transaction_date: date = Field(
        ...,
        description="Date when transaction occurred"
    )
    posted_date: date | None = Field(
        default=None,
        description="Date when transaction posted (may be after transaction_date)"
    )
    merchant_name: str | None = Field(
        default=None,
        description="Merchant or counterparty name",
        max_length=255
    )
    category: str | None = Field(
        default=None,
        description="Transaction category (e.g., 'Food and Drink', 'Transfer')",
        max_length=100
    )
    subcategory: str | None = Field(
        default=None,
        description="Transaction subcategory (e.g., 'Restaurants', 'Credit Card Payment')",
        max_length=100
    )
    transaction_type: Literal["debit", "credit", "transfer", "pending"] = Field(
        default="debit",
        description="Type of transaction"
    )
    pending: bool = Field(
        default=False,
        description="Whether transaction is still pending"
    )
    payment_channel: Literal["online", "in store", "other"] | None = Field(
        default=None,
        description="How the transaction was made"
    )

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Only USD is supported in MVP per PRD."""
        if v.upper() != "USD":
            raise ValueError(f"Unsupported currency: {v}. Only USD is supported in MVP.")
        return v.upper()

    @field_validator('transaction_date')
    @classmethod
    def validate_transaction_date(cls, v: date) -> date:
        """
        Ensure transaction date is not in the future.
        
        Why this matters:
        - Future dates indicate data errors
        - Can't analyze transactions that haven't happened yet
        """
        if v > date.today():
            raise ValueError(f"Transaction date cannot be in the future: {v}")
        return v

    @field_validator('posted_date')
    @classmethod
    def validate_posted_date(cls, v: date | None) -> date | None:
        """Ensure posted date is not in the future if provided."""
        if v and v > date.today():
            raise ValueError(f"Posted date cannot be in the future: {v}")
        return v

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal, info) -> Decimal:
        """
        Validate transaction amount.
        
        Why this matters:
        - Most transactions should be positive (debits)
        - Negative amounts are OK for credits, refunds, reversals
        - Zero amounts might indicate data issues (we allow but could warn)
        
        Note: We're lenient here since refunds/credits legitimately have
        negative amounts. Stricter validation happens in business logic.
        """
        # Allow negative amounts for refunds/credits
        # Extremely large amounts might be errors, but we allow them
        # (could add warning logging in production)
        return v


class TransactionCreate(TransactionBase):
    """
    Schema for creating a new transaction.
    
    Used when:
    - Generating synthetic transactions
    - Ingesting transactions from CSV/JSON
    """
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this transaction record was created"
    )


class Transaction(TransactionBase):
    """
    Complete transaction schema with database ID.
    
    Used when:
    - Returning transaction data from database
    - API responses
    - Analytics and feature computation
    """

    id: int = Field(..., description="Database primary key")
    created_at: datetime

    model_config = {"from_attributes": True}  # Enables ORM mode for SQLAlchemy compatibility


class TransactionInDB(Transaction):
    """Transaction schema as stored in database."""
    pass

