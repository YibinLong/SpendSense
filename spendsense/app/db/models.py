"""
SQLAlchemy ORM models for SpendSense database.

This defines all database tables using SQLAlchemy 2.0 syntax.

Why this exists:
- Provides type-safe database models with mypy compatibility
- Defines relationships between tables
- Enables ORM queries and automatic SQL generation
- Matches Pydantic schemas for validation

Tables:
- users: Core user data
- accounts: Bank accounts (checking, savings, credit)
- transactions: All financial transactions
- liabilities: Credit cards and loans
- consent_events: Consent tracking
- personas: User personas (stub for future)
- recommendations: Recommended content (stub for future)
- operator_reviews: Operator decisions (stub for future)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    
    Why we use DeclarativeBase (SQLAlchemy 2.0):
    - Modern type-safe ORM with Mapped[] syntax
    - Better mypy integration
    - Cleaner code vs old declarative_base()
    """
    pass


class User(Base):
    """
    User table - core user data.
    
    Why we need this:
    - Central entity linking all user financial data
    - Masked identifiers protect PII
    - Foundation for persona assignment and recommendations
    """
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User identifiers (masked, no real PII)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email_masked: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_masked: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships to other tables
    # These enable ORM queries like: user.accounts, user.transactions
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    liabilities: Mapped[List["Liability"]] = relationship("Liability", back_populates="user", cascade="all, delete-orphan")
    consent_events: Mapped[List["ConsentEvent"]] = relationship("ConsentEvent", back_populates="user", cascade="all, delete-orphan")
    personas: Mapped[List["Persona"]] = relationship("Persona", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, user_id='{self.user_id}')>"


class Account(Base):
    """
    Account table - bank accounts (checking, savings, credit).
    
    Why we need this:
    - Links transactions to users
    - Tracks balances and credit limits
    - Filters business accounts (holder_category)
    """
    __tablename__ = "accounts"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Account identifiers
    account_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Account details
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)  # depository, credit, loan, investment
    account_subtype: Mapped[str] = mapped_column(String(50), nullable=False)  # checking, savings, credit card, etc.
    holder_category: Mapped[str] = mapped_column(String(20), nullable=False, default="individual")  # individual, business, unknown
    
    # Financial data
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    balance_current: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_available: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Account(id={self.id}, account_id='{self.account_id}', type='{self.account_type}')>"


class Transaction(Base):
    """
    Transaction table - all financial transactions.
    
    Why we need this:
    - Core data for behavioral signal detection
    - Enables feature computation (subscriptions, savings, etc.)
    - Foundation for persona assignment
    """
    __tablename__ = "transactions"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction identifiers
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(100), ForeignKey("accounts.account_id"), nullable=False, index=True)
    
    # Transaction details
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    posted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Merchant and categorization
    merchant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Transaction metadata
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, default="debit")  # debit, credit, transfer, pending
    pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payment_channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # online, in store, other
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, amount={self.amount}, merchant='{self.merchant_name}', date={self.transaction_date})>"


# Index for common query pattern: transactions by account and date range
Index("idx_transactions_account_date", Transaction.account_id, Transaction.transaction_date)


class Liability(Base):
    """
    Liability table - credit cards and loans.
    
    Why we need this:
    - Tracks credit utilization for High Utilization persona
    - Monitors minimum payments and interest charges
    - Supports overdue detection
    """
    __tablename__ = "liabilities"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Liability identifiers
    liability_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Liability details
    liability_type: Mapped[str] = mapped_column(String(50), nullable=False)  # credit_card, student_loan, mortgage, etc.
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Financial data
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    minimum_payment: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    
    # Payment tracking
    last_payment_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    last_payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_payment_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Interest and status
    interest_rate_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="liabilities")
    
    def __repr__(self) -> str:
        return f"<Liability(id={self.id}, type='{self.liability_type}', balance={self.current_balance})>"


class ConsentEvent(Base):
    """
    Consent event table - tracks opt-in/opt-out actions.
    
    Why we need this:
    - PRD requires explicit consent before processing
    - Supports consent revocation
    - Full audit trail for compliance
    - Enables consent guardrails (403 blocking)
    """
    __tablename__ = "consent_events"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Consent details
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # opt_in, opt_out
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    consent_given_by: Mapped[str] = mapped_column(String(100), nullable=False)  # user_dashboard, api, operator
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="consent_events")
    
    def __repr__(self) -> str:
        return f"<ConsentEvent(id={self.id}, user_id='{self.user_id}', action='{self.action}', timestamp={self.timestamp})>"


# Index for finding latest consent per user
Index("idx_consent_user_timestamp", ConsentEvent.user_id, ConsentEvent.timestamp.desc())


class Persona(Base):
    """
    Persona table - assigned user personas (stub for future).
    
    Why we need this:
    - Stores persona assignments per user per window (30d, 180d)
    - Includes rationale for explainability
    - Foundation for recommendations
    
    Will be fully implemented in Persona System epic.
    """
    __tablename__ = "personas"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Persona assignment
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(50), nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 30 or 180
    
    # Explainability
    criteria_met: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON of criteria
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="personas")
    
    def __repr__(self) -> str:
        return f"<Persona(id={self.id}, user_id='{self.user_id}', persona='{self.persona_id}', window={self.window_days}d)>"


class Recommendation(Base):
    """
    Recommendation table - recommended education and offers (stub for future).
    
    Why we need this:
    - Stores personalized recommendations with rationales
    - Tracks eligibility and guardrail decisions
    - Enables operator review workflow
    
    Will be fully implemented in Recommendations epic.
    """
    __tablename__ = "recommendations"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Recommendation details
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    persona_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # education, offer
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Guardrails
    eligibility_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    disclosure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, approved, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, type='{self.item_type}', user='{self.user_id}')>"


class OperatorReview(Base):
    """
    Operator review table - operator decisions on recommendations (stub for future).
    
    Why we need this:
    - Tracks operator approve/override actions
    - Provides decision traceability
    - Enables audit trail for recommendations
    
    Will be fully implemented in Operator View epic.
    """
    __tablename__ = "operator_reviews"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Review details
    recommendation_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendations.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # approved, rejected, flagged
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<OperatorReview(id={self.id}, recommendation={self.recommendation_id}, status='{self.status}')>"


class SubscriptionSignal(Base):
    """
    Subscription signal table - stores computed subscription behavior signals.
    
    Why we need this:
    - Fast API access to subscription metrics without Parquet
    - Enables quick dashboard queries
    - Tracks recurring merchant patterns over time windows
    - Foundation for Subscription-Heavy persona assignment
    
    Computed from transactions in Feature Engineering epic.
    """
    __tablename__ = "subscription_signals"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User and window
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 30 or 180
    
    # Subscription metrics
    recurring_merchant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_recurring_spend: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    subscription_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    # Timestamp
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<SubscriptionSignal(user='{self.user_id}', window={self.window_days}d, merchants={self.recurring_merchant_count})>"


# Unique constraint: one signal per user per window
Index("idx_subscription_user_window", SubscriptionSignal.user_id, SubscriptionSignal.window_days, unique=True)


class SavingsSignal(Base):
    """
    Savings signal table - stores computed savings behavior signals.
    
    Why we need this:
    - Fast API access to savings metrics
    - Tracks emergency fund coverage and growth
    - Foundation for Savings Builder persona assignment
    
    Computed from savings accounts and transactions.
    """
    __tablename__ = "savings_signals"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User and window
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 30 or 180
    
    # Savings metrics
    savings_net_inflow: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    savings_growth_rate_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    emergency_fund_months: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    # Timestamp
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<SavingsSignal(user='{self.user_id}', window={self.window_days}d, emergency_fund={self.emergency_fund_months}mo)>"


# Unique constraint: one signal per user per window
Index("idx_savings_user_window", SavingsSignal.user_id, SavingsSignal.window_days, unique=True)


class CreditSignal(Base):
    """
    Credit signal table - stores computed credit utilization and behavior signals.
    
    Why we need this:
    - Fast API access to credit metrics
    - Tracks utilization thresholds and payment patterns
    - Foundation for High Utilization persona assignment
    
    Computed from liabilities and transactions.
    """
    __tablename__ = "credit_signals"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User and window
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 30 or 180
    
    # Utilization metrics
    credit_utilization_max_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    credit_utilization_avg_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    # Utilization flags
    credit_util_flag_30: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    credit_util_flag_50: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    credit_util_flag_80: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Behavior flags
    has_interest_charges: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_minimum_payment_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_overdue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Timestamp
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<CreditSignal(user='{self.user_id}', window={self.window_days}d, max_util={self.credit_utilization_max_pct}%)>"


# Unique constraint: one signal per user per window
Index("idx_credit_user_window", CreditSignal.user_id, CreditSignal.window_days, unique=True)


class IncomeSignal(Base):
    """
    Income signal table - stores computed income stability signals.
    
    Why we need this:
    - Fast API access to income metrics
    - Tracks payroll frequency and cash-flow buffer
    - Foundation for Variable Income Budgeter persona assignment
    
    Computed from income transactions and checking accounts.
    """
    __tablename__ = "income_signals"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User and window
    user_id: Mapped[str] = mapped_column(String(100), ForeignKey("users.user_id"), nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)  # 30 or 180
    
    # Payroll metrics
    payroll_deposit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    median_pay_gap_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    pay_gap_variability: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    avg_payroll_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    
    # Cash-flow metrics
    cashflow_buffer_months: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    # Timestamp
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<IncomeSignal(user='{self.user_id}', window={self.window_days}d, payrolls={self.payroll_deposit_count}, buffer={self.cashflow_buffer_months}mo)>"


# Unique constraint: one signal per user per window
Index("idx_income_user_window", IncomeSignal.user_id, IncomeSignal.window_days, unique=True)

