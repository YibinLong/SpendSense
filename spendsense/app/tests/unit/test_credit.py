"""
Unit tests for credit signal detection.

These tests verify the credit feature module works correctly for:
- Calculating utilization per card (balance / limit * 100)
- Flagging cards at 30%, 50%, 80% thresholds
- Detecting interest charges in transactions
- Detecting minimum-payment-only behavior
- Detecting overdue liabilities
- Handling edge cases (no credit cards, zero limit, missing payment data)
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import Base, User, Account, Transaction, Liability
from spendsense.app.features.credit import (
    compute_credit_utilization,
    check_credit_flags,
    compute_credit_signals
)


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
def user_with_credit_card(in_memory_db):
    """
    Create a user with a checking account and one credit card.
    
    Why this fixture:
    - Most credit tests need at least one credit card liability
    - Simulates typical user with one credit card
    """
    user = User(user_id="user_credit_001", email_masked="test@example.com")
    in_memory_db.add(user)
    
    account = Account(
        account_id="acc_credit_001",
        user_id="user_credit_001",
        account_name="Visa Credit Card",
        account_type="credit",
        account_subtype="credit card",
        holder_category="individual",
        balance_current=Decimal("500.00"),
        credit_limit=Decimal("2000.00")
    )
    in_memory_db.add(account)
    
    liability = Liability(
        liability_id="liab_001",
        user_id="user_credit_001",
        account_id="acc_credit_001",
        liability_type="credit_card",
        name="Visa Card",
        current_balance=Decimal("500.00"),
        credit_limit=Decimal("2000.00"),
        minimum_payment=Decimal("25.00"),
        is_overdue=False
    )
    in_memory_db.add(liability)
    
    in_memory_db.commit()
    
    return user, account, liability


def test_compute_utilization_normal_case(in_memory_db, user_with_credit_card):
    """
    Test calculating utilization for a normal credit card.
    
    Why this test matters:
    - Core functionality for High Utilization persona
    - Formula: (balance / limit) * 100
    - $500 / $2000 = 25% utilization
    """
    user, account, liability = user_with_credit_card
    
    liabilities = [liability]
    transactions = []
    
    result = compute_credit_utilization(liabilities, transactions)
    
    # Should be 25% utilization ($500 / $2000)
    assert abs(result["max_pct"] - 25.0) < 0.1
    assert abs(result["avg_pct"] - 25.0) < 0.1
    assert result["flag_30"] is False
    assert result["flag_50"] is False
    assert result["flag_80"] is False


def test_compute_utilization_flags_30_percent(in_memory_db, user_with_credit_card):
    """
    Test that 30% utilization flag is set correctly.
    
    Why this test matters:
    - 30% is important threshold for credit health
    - Users above 30% may see credit score impact
    """
    user, account, liability = user_with_credit_card
    
    # Update to 35% utilization ($700 / $2000)
    liability.current_balance = Decimal("700.00")
    in_memory_db.commit()
    
    result = compute_credit_utilization([liability], [])
    
    assert result["flag_30"] is True
    assert result["flag_50"] is False
    assert result["flag_80"] is False


def test_compute_utilization_flags_50_percent(in_memory_db, user_with_credit_card):
    """
    Test that 50% utilization flag triggers High Utilization persona.
    
    Why this test matters:
    - PRD Persona 1 criteria: any card utilization ≥50%
    - This is a critical threshold for persona assignment
    """
    user, account, liability = user_with_credit_card
    
    # Update to 60% utilization ($1200 / $2000)
    liability.current_balance = Decimal("1200.00")
    in_memory_db.commit()
    
    result = compute_credit_utilization([liability], [])
    
    assert result["flag_30"] is True
    assert result["flag_50"] is True  # Triggers persona
    assert result["flag_80"] is False


def test_compute_utilization_flags_80_percent(in_memory_db, user_with_credit_card):
    """
    Test that 80% utilization flag indicates high financial stress.
    
    Why this test matters:
    - 80%+ utilization is severe
    - Indicates user is near credit limit
    - May trigger urgent recommendations
    """
    user, account, liability = user_with_credit_card
    
    # Update to 90% utilization ($1800 / $2000)
    liability.current_balance = Decimal("1800.00")
    in_memory_db.commit()
    
    result = compute_credit_utilization([liability], [])
    
    assert result["flag_30"] is True
    assert result["flag_50"] is True
    assert result["flag_80"] is True  # High stress


def test_compute_utilization_multiple_cards(in_memory_db):
    """
    Test utilization calculation with multiple credit cards.
    
    Why this test matters:
    - Many users have multiple cards
    - Should track max and average utilization
    - Flags trigger if ANY card meets threshold
    """
    user = User(user_id="user_multi_cards", email_masked="test@example.com")
    in_memory_db.add(user)
    
    # Card 1: 25% utilization ($500 / $2000)
    liab1 = Liability(
        liability_id="liab_card1",
        user_id="user_multi_cards",
        liability_type="credit_card",
        name="Card 1",
        current_balance=Decimal("500.00"),
        credit_limit=Decimal("2000.00")
    )
    in_memory_db.add(liab1)
    
    # Card 2: 60% utilization ($1200 / $2000) - triggers 50% flag
    liab2 = Liability(
        liability_id="liab_card2",
        user_id="user_multi_cards",
        liability_type="credit_card",
        name="Card 2",
        current_balance=Decimal("1200.00"),
        credit_limit=Decimal("2000.00")
    )
    in_memory_db.add(liab2)
    
    in_memory_db.commit()
    
    result = compute_credit_utilization([liab1, liab2], [])
    
    # Max should be 60% (Card 2)
    assert abs(result["max_pct"] - 60.0) < 0.1
    # Average should be (25% + 60%) / 2 = 42.5%
    assert abs(result["avg_pct"] - 42.5) < 0.1
    # flag_50 should be True because Card 2 is at 60%
    assert result["flag_50"] is True


def test_compute_utilization_zero_limit(in_memory_db):
    """
    Test handling credit card with zero or missing limit.
    
    Why this test matters:
    - Edge case: card without limit data
    - Should skip card, not crash with division by zero
    """
    user = User(user_id="user_no_limit", email_masked="test@example.com")
    in_memory_db.add(user)
    
    # Card with zero limit
    liab = Liability(
        liability_id="liab_no_limit",
        user_id="user_no_limit",
        liability_type="credit_card",
        name="Card",
        current_balance=Decimal("500.00"),
        credit_limit=Decimal("0.00")  # Zero limit
    )
    in_memory_db.add(liab)
    in_memory_db.commit()
    
    result = compute_credit_utilization([liab], [])
    
    # Should return zeros (card skipped)
    assert result["max_pct"] == 0.0
    assert result["avg_pct"] == 0.0
    assert result["flag_30"] is False


def test_detect_interest_charges(in_memory_db, user_with_credit_card):
    """
    Test detecting interest charges in transactions.
    
    Why this test matters:
    - PRD Persona 1 criteria: interest > 0
    - Interest charges mean user is carrying a balance
    - Indicates not paying in full each month
    """
    user, account, liability = user_with_credit_card
    
    # Create interest charge transaction
    tx = Transaction(
        transaction_id="tx_interest",
        account_id=account.account_id,
        amount=Decimal("15.00"),
        transaction_date=date.today() - timedelta(days=5),
        merchant_name="Interest Charge",  # Special merchant name
        category="Payment",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    result = check_credit_flags([liability], transactions)
    
    assert result["has_interest_charges"] is True


def test_detect_minimum_payment_only(in_memory_db, user_with_credit_card):
    """
    Test detecting minimum-payment-only behavior.
    
    Why this test matters:
    - PRD Persona 1 criteria: minimum-payment-only
    - Indicates financial stress (can't pay more than minimum)
    - 10% tolerance accounts for rounding variations
    """
    user, account, liability = user_with_credit_card
    
    # Set last payment to minimum payment ($25)
    liability.minimum_payment = Decimal("25.00")
    liability.last_payment_amount = Decimal("25.00")  # Exactly minimum
    in_memory_db.commit()
    
    result = check_credit_flags([liability], [])
    
    assert result["has_minimum_payment_only"] is True


def test_minimum_payment_with_tolerance(in_memory_db, user_with_credit_card):
    """
    Test minimum payment detection with 10% tolerance.
    
    Why this test matters:
    - Validates 10% tolerance rule
    - User paying $27 when minimum is $25 = still minimum-only
    - Prevents false negatives from small variations
    """
    user, account, liability = user_with_credit_card
    
    # Last payment is within 10% of minimum ($27 vs $25)
    liability.minimum_payment = Decimal("25.00")
    liability.last_payment_amount = Decimal("27.00")  # 108% of minimum (within 110%)
    in_memory_db.commit()
    
    result = check_credit_flags([liability], [])
    
    assert result["has_minimum_payment_only"] is True  # Within tolerance


def test_not_minimum_payment_only(in_memory_db, user_with_credit_card):
    """
    Test that larger payments don't trigger minimum-only flag.
    
    Why this test matters:
    - Validates users paying more than minimum are not flagged
    - Payment significantly above minimum (>110%) = not minimum-only
    """
    user, account, liability = user_with_credit_card
    
    # Last payment well above minimum ($100 vs $25)
    liability.minimum_payment = Decimal("25.00")
    liability.last_payment_amount = Decimal("100.00")  # 400% of minimum
    in_memory_db.commit()
    
    result = check_credit_flags([liability], [])
    
    assert result["has_minimum_payment_only"] is False


def test_detect_overdue(in_memory_db, user_with_credit_card):
    """
    Test detecting overdue liability status.
    
    Why this test matters:
    - PRD Persona 1 criteria: overdue
    - Immediate financial distress signal
    - Most severe credit issue
    """
    user, account, liability = user_with_credit_card
    
    # Mark as overdue
    liability.is_overdue = True
    in_memory_db.commit()
    
    result = check_credit_flags([liability], [])
    
    assert result["is_overdue"] is True


def test_compute_credit_signals_no_cards(in_memory_db):
    """
    Test computing credit signals when user has no credit cards.
    
    Why this test matters:
    - Edge case: user doesn't have any credit cards
    - Should return zeros and False flags
    """
    user = User(user_id="user_no_credit", email_masked="test@example.com")
    in_memory_db.add(user)
    in_memory_db.commit()
    
    signal = compute_credit_signals("user_no_credit", 30, in_memory_db)
    
    assert signal.credit_utilization_max_pct == Decimal("0.00")
    assert signal.credit_utilization_avg_pct == Decimal("0.00")
    assert signal.credit_util_flag_30 is False
    assert signal.credit_util_flag_50 is False
    assert signal.credit_util_flag_80 is False
    assert signal.has_interest_charges is False
    assert signal.has_minimum_payment_only is False
    assert signal.is_overdue is False


def test_compute_credit_signals_meets_persona_criteria(in_memory_db, user_with_credit_card):
    """
    Test that signals meet High Utilization persona criteria.
    
    Why this test matters:
    - Validates integration with persona assignment
    - PRD Persona 1: utilization ≥50% OR interest > 0 OR minimum-only OR overdue
    - This test creates multiple triggers
    """
    user, account, liability = user_with_credit_card
    
    # Set 60% utilization
    liability.current_balance = Decimal("1200.00")
    liability.credit_limit = Decimal("2000.00")
    
    # Add interest charge
    tx = Transaction(
        transaction_id="tx_interest",
        account_id=account.account_id,
        amount=Decimal("20.00"),
        transaction_date=date.today() - timedelta(days=5),
        merchant_name="Interest Charge",
        category="Payment",
        transaction_type="debit"
    )
    in_memory_db.add(tx)
    
    # Set minimum-only payment
    liability.minimum_payment = Decimal("25.00")
    liability.last_payment_amount = Decimal("25.00")
    
    in_memory_db.commit()
    
    signal = compute_credit_signals("user_credit_001", 30, in_memory_db)
    
    # Should meet ALL criteria
    assert signal.credit_util_flag_50 is True  # Criterion 1
    assert signal.has_interest_charges is True  # Criterion 2
    assert signal.has_minimum_payment_only is True  # Criterion 3


def test_compute_credit_signals_normal_user(in_memory_db, user_with_credit_card):
    """
    Test credit signals for a healthy credit user.
    
    Why this test matters:
    - Validates signals for users NOT meeting High Utilization criteria
    - Low utilization, no interest, paying more than minimum = healthy
    """
    user, account, liability = user_with_credit_card
    
    # Low utilization (15%)
    liability.current_balance = Decimal("300.00")
    liability.credit_limit = Decimal("2000.00")
    
    # Paying well above minimum
    liability.minimum_payment = Decimal("25.00")
    liability.last_payment_amount = Decimal("200.00")
    
    in_memory_db.commit()
    
    signal = compute_credit_signals("user_credit_001", 30, in_memory_db)
    
    # Should NOT meet High Utilization criteria
    assert signal.credit_util_flag_30 is False
    assert signal.credit_util_flag_50 is False
    assert signal.has_interest_charges is False
    assert signal.has_minimum_payment_only is False
    assert signal.is_overdue is False

