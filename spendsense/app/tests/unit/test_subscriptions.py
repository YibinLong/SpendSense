"""
Unit tests for subscription signal detection.

These tests verify the subscription feature module works correctly for:
- Detecting recurring merchants (≥3 occurrences)
- Computing monthly recurring spend
- Calculating subscription share percentage
- Handling edge cases (no subscriptions, refunds, pending transactions, sparse data)
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import Account, Base, Transaction, User
from spendsense.app.features.subscriptions import compute_subscription_signals, detect_recurring_merchants


@pytest.fixture
def in_memory_db():
    """
    Create an in-memory SQLite database for testing.
    
    Why in-memory:
    - Fast (no disk I/O)
    - Isolated (each test gets fresh database)
    - No cleanup needed (database disappears after test)
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def sample_user(in_memory_db):
    """Create a sample user with a checking account."""
    user = User(user_id="user_test_001", email_masked="test@example.com")
    in_memory_db.add(user)

    account = Account(
        account_id="acc_test_001",
        user_id="user_test_001",
        account_name="Test Checking",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        balance_current=Decimal("1000.00")
    )
    in_memory_db.add(account)
    in_memory_db.commit()

    return user, account


def test_detect_recurring_merchants_with_valid_subscriptions(in_memory_db, sample_user):
    """
    Test detecting recurring merchants with ≥3 occurrences.
    
    Why this test matters:
    - Core functionality for Subscription-Heavy persona
    - PRD requires ≥3 occurrences to identify subscriptions
    """
    user, account = sample_user

    # Create 3 Netflix transactions (should be detected)
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_netflix_{i}",
            account_id=account.account_id,
            amount=Decimal("14.99"),
            transaction_date=date.today() - timedelta(days=i*30),
            merchant_name="Netflix",
            category="Subscription",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    # Create 2 Spotify transactions (should NOT be detected - only 2)
    for i in range(2):
        tx = Transaction(
            transaction_id=f"tx_spotify_{i}",
            account_id=account.account_id,
            amount=Decimal("9.99"),
            transaction_date=date.today() - timedelta(days=i*30),
            merchant_name="Spotify",
            category="Subscription",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    # Get all transactions
    transactions = in_memory_db.query(Transaction).all()

    # Detect recurring merchants
    recurring = detect_recurring_merchants(transactions, window_days=90)

    # Should only detect Netflix (≥3 occurrences)
    assert len(recurring) == 1
    assert "Netflix" in recurring
    assert "Spotify" not in recurring


def test_detect_recurring_merchants_no_subscriptions(in_memory_db, sample_user):
    """
    Test that no recurring merchants are detected when there are no subscription transactions.
    
    Why this test matters:
    - Edge case: user has no subscriptions
    - Should return empty list, not error
    """
    user, account = sample_user

    # Create non-subscription transactions
    tx = Transaction(
        transaction_id="tx_grocery_001",
        account_id=account.account_id,
        amount=Decimal("50.00"),
        transaction_date=date.today(),
        merchant_name="Whole Foods",
        category="Food and Drink",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()

    transactions = in_memory_db.query(Transaction).all()
    recurring = detect_recurring_merchants(transactions, window_days=30)

    assert len(recurring) == 0


def test_compute_subscription_signals_valid_data(in_memory_db, sample_user):
    """
    Test computing subscription signals with valid subscription data.
    
    Why this test matters:
    - Verifies all metrics are calculated correctly
    - Tests the complete flow from transactions to signals
    """
    user, account = sample_user

    # Create 3 Netflix subscriptions within 90-day window (spaced 10 days apart)
    # This ensures all 3 fall within the test window
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_netflix_{i}",
            account_id=account.account_id,
            amount=Decimal("14.99"),
            transaction_date=date.today() - timedelta(days=i*10),  # Changed from 30 to 10 days
            merchant_name="Netflix",
            category="Subscription",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    # Create some non-subscription spending (to test subscription share)
    for i in range(5):
        tx = Transaction(
            transaction_id=f"tx_grocery_{i}",
            account_id=account.account_id,
            amount=Decimal("100.00"),
            transaction_date=date.today() - timedelta(days=i*6),
            merchant_name="Whole Foods",
            category="Food and Drink",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    # Compute signals for 90-day window to capture all Netflix transactions
    signal = compute_subscription_signals("user_test_001", 90, in_memory_db)

    # Verify signal attributes
    assert signal.user_id == "user_test_001"
    assert signal.window_days == 90
    assert signal.recurring_merchant_count == 1  # Netflix (≥3 occurrences)
    assert signal.monthly_recurring_spend > 0
    assert signal.subscription_share_pct > 0
    assert signal.subscription_share_pct < 100  # Not all spending is subscriptions


def test_compute_subscription_signals_no_accounts(in_memory_db):
    """
    Test computing subscription signals when user has no accounts.
    
    Why this test matters:
    - Edge case: new user with no accounts yet
    - Should return zeros, not crash
    """
    # Create user without accounts
    user = User(user_id="user_no_accounts", email_masked="test@example.com")
    in_memory_db.add(user)
    in_memory_db.commit()

    signal = compute_subscription_signals("user_no_accounts", 30, in_memory_db)

    assert signal.user_id == "user_no_accounts"
    assert signal.recurring_merchant_count == 0
    assert signal.monthly_recurring_spend == Decimal("0.00")
    assert signal.subscription_share_pct == Decimal("0.00")


def test_compute_subscription_signals_no_transactions(in_memory_db, sample_user):
    """
    Test computing subscription signals when user has accounts but no transactions.
    
    Why this test matters:
    - Edge case: brand new account
    - Should return zeros gracefully
    """
    signal = compute_subscription_signals("user_test_001", 30, in_memory_db)

    assert signal.recurring_merchant_count == 0
    assert signal.monthly_recurring_spend == Decimal("0.00")
    assert signal.subscription_share_pct == Decimal("0.00")


def test_compute_subscription_signals_excludes_pending(in_memory_db, sample_user):
    """
    Test that pending transactions are excluded from subscription detection.
    
    Why this test matters:
    - PRD specifies pending transactions should be excluded
    - Prevents false positives from authorization holds
    """
    user, account = sample_user

    # Create 3 pending subscription transactions
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_pending_{i}",
            account_id=account.account_id,
            amount=Decimal("14.99"),
            transaction_date=date.today() - timedelta(days=i*30),
            merchant_name="Netflix",
            category="Subscription",
            transaction_type="debit",
            pending=True  # Marked as pending
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    signal = compute_subscription_signals("user_test_001", 90, in_memory_db)

    # Should NOT detect any recurring merchants (all are pending)
    assert signal.recurring_merchant_count == 0


def test_compute_subscription_signals_with_refunds(in_memory_db, sample_user):
    """
    Test subscription detection with refund transactions.
    
    Why this test matters:
    - Refunds (negative amounts for debits) are edge cases
    - Should handle refunds without crashing
    - Refunds count as separate transactions in detection
    """
    user, account = sample_user

    # Create 3 regular Netflix charges
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_netflix_{i}",
            account_id=account.account_id,
            amount=Decimal("14.99"),
            transaction_date=date.today() - timedelta(days=i*30),
            merchant_name="Netflix",
            category="Subscription",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    # Create 1 Netflix refund (negative amount)
    tx_refund = Transaction(
        transaction_id="tx_netflix_refund",
        account_id=account.account_id,
        amount=Decimal("-14.99"),  # Refund
        transaction_date=date.today() - timedelta(days=45),
        merchant_name="Netflix",
        category="Subscription",
        transaction_type="credit"
    )
    in_memory_db.add(tx_refund)

    in_memory_db.commit()

    signal = compute_subscription_signals("user_test_001", 90, in_memory_db)

    # Should detect Netflix as recurring (4 total transactions including refund)
    assert signal.recurring_merchant_count == 1
    # Monthly spend should account for the refund
    assert signal.monthly_recurring_spend < Decimal("15.00")


def test_compute_subscription_signals_sparse_data(in_memory_db, sample_user):
    """
    Test subscription detection with very sparse transaction data.
    
    Why this test matters:
    - Edge case: user with minimal activity
    - Should handle gracefully without division errors
    """
    user, account = sample_user

    # Create only 1 subscription transaction
    tx = Transaction(
        transaction_id="tx_single",
        account_id=account.account_id,
        amount=Decimal("9.99"),
        transaction_date=date.today(),
        merchant_name="Spotify",
        category="Subscription",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()

    signal = compute_subscription_signals("user_test_001", 30, in_memory_db)

    # Should NOT detect as recurring (only 1 occurrence)
    assert signal.recurring_merchant_count == 0
    # But should still calculate monthly spend
    assert signal.monthly_recurring_spend > 0


def test_subscription_share_calculation(in_memory_db, sample_user):
    """
    Test that subscription share percentage is calculated correctly.
    
    Why this test matters:
    - Subscription share is a key metric for Subscription-Heavy persona
    - PRD criteria: subscription share ≥10%
    """
    user, account = sample_user

    # Create $30 in subscriptions
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_sub_{i}",
            account_id=account.account_id,
            amount=Decimal("10.00"),
            transaction_date=date.today() - timedelta(days=i*10),
            merchant_name="Service",
            category="Subscription",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    # Create $270 in other spending (total = $300)
    for i in range(27):
        tx = Transaction(
            transaction_id=f"tx_other_{i}",
            account_id=account.account_id,
            amount=Decimal("10.00"),
            transaction_date=date.today() - timedelta(days=i),
            merchant_name="Store",
            category="Shopping",
            transaction_type="debit"
        )
        in_memory_db.add(tx)

    in_memory_db.commit()

    signal = compute_subscription_signals("user_test_001", 30, in_memory_db)

    # Subscription share should be 10% (30/300)
    assert abs(float(signal.subscription_share_pct) - 10.0) < 0.1  # Allow small floating point error

