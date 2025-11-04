"""
Unit tests for savings signal detection.

These tests verify the savings feature module works correctly for:
- Computing net inflow to savings accounts
- Calculating savings growth rate percentage
- Calculating emergency fund coverage (months)
- Handling edge cases (no savings account, division by zero, negative growth)
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import Account, Base, Transaction, User
from spendsense.app.features.savings import compute_savings_signals


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def user_with_savings(in_memory_db):
    """
    Create a user with checking and savings accounts.
    
    Why this fixture:
    - Most savings tests need both checking (for expenses) and savings accounts
    - Simulates realistic account structure
    """
    user = User(user_id="user_savings_001", email_masked="test@example.com")
    in_memory_db.add(user)

    # Checking account
    checking = Account(
        account_id="acc_checking_001",
        user_id="user_savings_001",
        account_name="Test Checking",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        balance_current=Decimal("2000.00")
    )
    in_memory_db.add(checking)

    # Savings account
    savings = Account(
        account_id="acc_savings_001",
        user_id="user_savings_001",
        account_name="Test Savings",
        account_type="depository",
        account_subtype="savings",
        holder_category="individual",
        balance_current=Decimal("3000.00")
    )
    in_memory_db.add(savings)

    in_memory_db.commit()

    return user, checking, savings


def test_compute_net_inflow_positive(in_memory_db, user_with_savings):
    """
    Test computing positive net inflow to savings (user is saving money).
    
    Why this test matters:
    - Core metric for Savings Builder persona
    - Positive inflow means user is building emergency fund
    """
    user, checking, savings = user_with_savings

    # Create deposits to savings (credits are negative in Plaid convention)
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_deposit_{i}",
            account_id=savings.account_id,
            amount=Decimal("-200.00"),  # Credit (deposit)
            transaction_date=date.today() - timedelta(days=i*10),
            merchant_name="Transfer from Checking",
            category="Transfer",
            transaction_type="credit"
        )
        in_memory_db.add(tx)

    # Create one withdrawal from savings (debit is positive)
    tx_withdraw = Transaction(
        transaction_id="tx_withdraw_001",
        account_id=savings.account_id,
        amount=Decimal("100.00"),  # Debit (withdrawal)
        transaction_date=date.today() - timedelta(days=15),
        merchant_name="ATM Withdrawal",
        category="Transfer",
        transaction_type="debit"
    )
    in_memory_db.add(tx_withdraw)

    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Net inflow = 3*$200 (deposits) - $100 (withdrawal) = $500
    assert signal.savings_net_inflow == Decimal("500.00")
    assert signal.savings_net_inflow > 0  # Positive = saving


def test_compute_net_inflow_negative(in_memory_db, user_with_savings):
    """
    Test computing negative net inflow (user is depleting savings).
    
    Why this test matters:
    - Edge case: user spending from savings
    - Negative inflow should be handled without errors
    - Indicates financial stress
    """
    user, checking, savings = user_with_savings

    # Create large withdrawal
    tx = Transaction(
        transaction_id="tx_large_withdraw",
        account_id=savings.account_id,
        amount=Decimal("500.00"),  # Debit (withdrawal)
        transaction_date=date.today() - timedelta(days=5),
        merchant_name="Emergency Expense",
        category="Transfer",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Net inflow should be negative (user depleting savings)
    assert signal.savings_net_inflow < 0


def test_compute_growth_rate(in_memory_db, user_with_savings):
    """
    Test calculating savings growth rate percentage.
    
    Why this test matters:
    - PRD Persona 4 criteria: savings growth ≥2% over window
    - Growth rate = (net inflow / starting balance) * 100
    """
    user, checking, savings = user_with_savings

    # Current balance is $3000
    # Add $150 in deposits (5% growth if starting balance was $3000 - $150 = $2850)
    tx = Transaction(
        transaction_id="tx_deposit",
        account_id=savings.account_id,
        amount=Decimal("-150.00"),  # Credit
        transaction_date=date.today() - timedelta(days=15),
        merchant_name="Transfer",
        category="Transfer",
        transaction_type="credit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Growth rate should be approximately 5% ($150 / $2850 * 100)
    assert signal.savings_growth_rate_pct > Decimal("2.00")  # Meets persona criteria
    assert signal.savings_growth_rate_pct < Decimal("10.00")  # Reasonable range


def test_emergency_fund_coverage(in_memory_db, user_with_savings):
    """
    Test calculating emergency fund coverage in months.
    
    Why this test matters:
    - Standard financial advice: 3-6 months emergency fund
    - Formula: savings balance / average monthly expenses
    - Key indicator of financial health
    """
    user, checking, savings = user_with_savings

    # Create monthly expenses totaling $1000/month
    # Over 30 days, create $1000 in expenses
    for i in range(10):
        tx = Transaction(
            transaction_id=f"tx_expense_{i}",
            account_id=checking.account_id,
            amount=Decimal("100.00"),  # $100 each = $1000 total
            transaction_date=date.today() - timedelta(days=i*3),
            merchant_name="Store",
            category="Shopping",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Emergency fund = $3000 / $1000 per month = 3 months
    assert abs(float(signal.emergency_fund_months) - 3.0) < 0.1  # Allow small floating point error


def test_no_savings_account(in_memory_db):
    """
    Test computing savings signals when user has no savings account.
    
    Why this test matters:
    - Edge case: user hasn't opened a savings account yet
    - Should return zeros, not crash
    """
    user = User(user_id="user_no_savings", email_masked="test@example.com")
    in_memory_db.add(user)

    # Only checking account, no savings
    checking = Account(
        account_id="acc_checking_002",
        user_id="user_no_savings",
        account_name="Checking",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        balance_current=Decimal("500.00")
    )
    in_memory_db.add(checking)
    in_memory_db.commit()

    signal = compute_savings_signals("user_no_savings", 30, in_memory_db)

    assert signal.savings_net_inflow == Decimal("0.00")
    assert signal.savings_growth_rate_pct == Decimal("0.00")
    assert signal.emergency_fund_months == Decimal("0.00")


def test_no_expenses_division_by_zero(in_memory_db, user_with_savings):
    """
    Test handling division by zero when there are no expenses.
    
    Why this test matters:
    - Edge case: brand new account with no activity
    - Emergency fund coverage requires expenses to calculate
    - Should handle gracefully without ZeroDivisionError
    """
    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # No transactions created, so no expenses
    # Emergency fund should be 0 (can't calculate without expenses)
    assert signal.emergency_fund_months == Decimal("0.00")


def test_negative_growth_rate(in_memory_db, user_with_savings):
    """
    Test negative growth rate when user depletes savings.
    
    Why this test matters:
    - Edge case: savings balance decreasing
    - Negative growth is valid (not an error)
    - Indicates financial difficulty
    """
    user, checking, savings = user_with_savings

    # Large withdrawal that exceeds deposits
    tx = Transaction(
        transaction_id="tx_withdraw",
        account_id=savings.account_id,
        amount=Decimal("1000.00"),  # Large withdrawal
        transaction_date=date.today() - timedelta(days=10),
        merchant_name="Emergency",
        category="Transfer",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Growth rate should be negative
    assert signal.savings_growth_rate_pct < Decimal("0.00")


def test_savings_with_no_accounts(in_memory_db):
    """
    Test computing savings signals when user has no accounts at all.
    
    Why this test matters:
    - Edge case: completely new user
    - Should return zeros gracefully
    """
    user = User(user_id="user_no_accounts", email_masked="test@example.com")
    in_memory_db.add(user)
    in_memory_db.commit()

    signal = compute_savings_signals("user_no_accounts", 30, in_memory_db)

    assert signal.user_id == "user_no_accounts"
    assert signal.savings_net_inflow == Decimal("0.00")
    assert signal.savings_growth_rate_pct == Decimal("0.00")
    assert signal.emergency_fund_months == Decimal("0.00")


def test_savings_meets_persona_criteria(in_memory_db, user_with_savings):
    """
    Test that signal values meet Savings Builder persona criteria.
    
    Why this test matters:
    - Verifies integration with persona assignment logic
    - PRD Persona 4 criteria: growth ≥2% OR net inflow ≥$200/month
    """
    user, checking, savings = user_with_savings

    # Create $250 in monthly savings (meets ≥$200/month criteria)
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_deposit_{i}",
            account_id=savings.account_id,
            amount=Decimal("-250.00"),  # $250 deposits
            transaction_date=date.today() - timedelta(days=i*10),
            merchant_name="Auto Transfer",
            category="Transfer",
            transaction_type="credit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Net inflow should be $750 total = $750/month in 30-day window
    # Monthly inflow = $750 / 1 month = $750
    assert signal.savings_net_inflow >= Decimal("200.00")  # Meets criteria

    # Growth rate should also be positive
    assert signal.savings_growth_rate_pct > Decimal("0.00")


def test_high_emergency_fund_coverage(in_memory_db, user_with_savings):
    """
    Test user with strong emergency fund (6+ months).
    
    Why this test matters:
    - Validates calculation for well-prepared users
    - 6 months is upper end of recommended emergency fund
    """
    user, checking, savings = user_with_savings

    # Update savings balance to $6000
    savings.balance_current = Decimal("6000.00")
    in_memory_db.commit()

    # Create $1000/month in expenses
    for i in range(10):
        tx = Transaction(
            transaction_id=f"tx_expense_{i}",
            account_id=checking.account_id,
            amount=Decimal("100.00"),
            transaction_date=date.today() - timedelta(days=i*3),
            merchant_name="Store",
            category="Shopping",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    signal = compute_savings_signals("user_savings_001", 30, in_memory_db)

    # Emergency fund = $6000 / $1000 = 6 months
    assert signal.emergency_fund_months >= Decimal("6.00")


