"""
Unit tests for income stability signal detection.

These tests verify the income feature module works correctly for:
- Detecting payroll transactions (category=Income, subcategory=Paycheck)
- Calculating median pay gap (days between paychecks)
- Calculating pay gap variability (standard deviation)
- Computing cash-flow buffer (checking balance / monthly expenses)
- Handling edge cases (irregular income, < 2 paychecks, zero expenses)
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import Base, User, Account, Transaction
from spendsense.app.features.income import (
    detect_payroll_transactions,
    compute_pay_frequency_stats,
    compute_income_signals
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
def user_with_checking(in_memory_db):
    """
    Create a user with a checking account.
    
    Why this fixture:
    - Income tests need checking account for payroll deposits
    - Cash-flow buffer uses checking balance
    """
    user = User(user_id="user_income_001", email_masked="test@example.com")
    in_memory_db.add(user)
    
    checking = Account(
        account_id="acc_checking_001",
        user_id="user_income_001",
        account_name="Checking",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        balance_current=Decimal("1500.00")
    )
    in_memory_db.add(checking)
    
    in_memory_db.commit()
    
    return user, checking


def test_detect_payroll_transactions(in_memory_db, user_with_checking):
    """
    Test detecting payroll transactions from mixed transaction data.
    
    Why this test matters:
    - Core functionality for income stability analysis
    - Must filter for category=Income, subcategory=Paycheck
    - Payroll is negative (credits in Plaid convention)
    """
    user, checking = user_with_checking
    
    # Create payroll transaction (should be detected)
    tx_payroll = Transaction(
        transaction_id="tx_payroll_001",
        account_id=checking.account_id,
        amount=Decimal("-2500.00"),  # Credit (negative)
        transaction_date=date.today(),
        merchant_name="Payroll ACH",
        category="Income",
        subcategory="Paycheck",
        transaction_type="credit"
    )
    in_memory_db.add(tx_payroll)
    
    # Create non-payroll income (should NOT be detected)
    tx_refund = Transaction(
        transaction_id="tx_refund_001",
        account_id=checking.account_id,
        amount=Decimal("-50.00"),
        transaction_date=date.today() - timedelta(days=5),
        merchant_name="Tax Refund",
        category="Income",
        subcategory="Tax Refund",  # Not "Paycheck"
        transaction_type="credit"
    )
    in_memory_db.add(tx_refund)
    
    # Create non-income transaction (should NOT be detected)
    tx_expense = Transaction(
        transaction_id="tx_expense_001",
        account_id=checking.account_id,
        amount=Decimal("100.00"),
        transaction_date=date.today() - timedelta(days=3),
        merchant_name="Store",
        category="Shopping",
        transaction_type="debit"
    )
    in_memory_db.add(tx_expense)
    
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    payroll_txs = detect_payroll_transactions(transactions)
    
    # Should only detect the payroll transaction
    assert len(payroll_txs) == 1
    assert payroll_txs[0].transaction_id == "tx_payroll_001"


def test_compute_pay_frequency_biweekly(in_memory_db, user_with_checking):
    """
    Test pay frequency calculation for bi-weekly payroll (14-day gaps).
    
    Why this test matters:
    - Bi-weekly is common payroll schedule
    - Median should be 14 days
    - Variability should be low (consistent schedule)
    """
    user, checking = user_with_checking
    
    # Create 4 bi-weekly paychecks (14 days apart)
    for i in range(4):
        tx = Transaction(
            transaction_id=f"tx_payroll_{i}",
            account_id=checking.account_id,
            amount=Decimal("-2000.00"),
            transaction_date=date.today() - timedelta(days=i*14),
            merchant_name="Payroll",
            category="Income",
            subcategory="Paycheck",
            transaction_type="credit"
        )
        in_memory_db.add(tx)
    
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    payroll_txs = detect_payroll_transactions(transactions)
    stats = compute_pay_frequency_stats(payroll_txs)
    
    # Median gap should be 14 days
    assert abs(stats["median_pay_gap_days"] - 14.0) < 0.1
    # Variability should be very low (consistent schedule)
    assert stats["pay_gap_variability"] < 1.0
    # Average payroll should be $2000
    assert abs(stats["avg_payroll_amount"] - 2000.0) < 0.1


def test_compute_pay_frequency_monthly(in_memory_db, user_with_checking):
    """
    Test pay frequency calculation for monthly payroll (30-day gaps).
    
    Why this test matters:
    - Monthly is another common payroll schedule
    - Median should be approximately 30 days
    """
    user, checking = user_with_checking
    
    # Create 3 monthly paychecks (30 days apart)
    for i in range(3):
        tx = Transaction(
            transaction_id=f"tx_payroll_{i}",
            account_id=checking.account_id,
            amount=Decimal("-3000.00"),
            transaction_date=date.today() - timedelta(days=i*30),
            merchant_name="Payroll",
            category="Income",
            subcategory="Paycheck",
            transaction_type="credit"
        )
        in_memory_db.add(tx)
    
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    payroll_txs = detect_payroll_transactions(transactions)
    stats = compute_pay_frequency_stats(payroll_txs)
    
    # Median gap should be approximately 30 days
    assert abs(stats["median_pay_gap_days"] - 30.0) < 0.1


def test_compute_pay_frequency_irregular(in_memory_db, user_with_checking):
    """
    Test pay frequency calculation for irregular income.
    
    Why this test matters:
    - Variable Income Budgeter persona targets irregular income
    - High variability indicates inconsistent pay schedule
    - PRD criteria: median pay gap > 45 days
    """
    user, checking = user_with_checking
    
    # Create irregular paycheck schedule: 20, 45, 60 day gaps
    paycheck_dates = [
        date.today(),
        date.today() - timedelta(days=20),
        date.today() - timedelta(days=65),  # 45 days before previous
        date.today() - timedelta(days=125)  # 60 days before previous
    ]
    
    for i, paycheck_date in enumerate(paycheck_dates):
        tx = Transaction(
            transaction_id=f"tx_payroll_{i}",
            account_id=checking.account_id,
            amount=Decimal("-2500.00"),
            transaction_date=paycheck_date,
            merchant_name="Payroll",
            category="Income",
            subcategory="Paycheck",
            transaction_type="credit"
        )
        in_memory_db.add(tx)
    
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    payroll_txs = detect_payroll_transactions(transactions)
    stats = compute_pay_frequency_stats(payroll_txs)
    
    # Median gap (middle of 20, 45, 60) should be 45 days
    assert abs(stats["median_pay_gap_days"] - 45.0) < 0.1
    # Variability should be high (inconsistent schedule)
    assert stats["pay_gap_variability"] > 10.0


def test_compute_pay_frequency_single_paycheck(in_memory_db, user_with_checking):
    """
    Test pay frequency with only 1 paycheck (can't calculate gaps).
    
    Why this test matters:
    - Edge case: new employee or data window too small
    - Should return zeros, not crash
    """
    user, checking = user_with_checking
    
    # Create only 1 paycheck
    tx = Transaction(
        transaction_id="tx_payroll_001",
        account_id=checking.account_id,
        amount=Decimal("-2000.00"),
        transaction_date=date.today(),
        merchant_name="Payroll",
        category="Income",
        subcategory="Paycheck",
        transaction_type="credit"
    )
    in_memory_db.add(tx)
    in_memory_db.commit()
    
    transactions = in_memory_db.query(Transaction).all()
    payroll_txs = detect_payroll_transactions(transactions)
    stats = compute_pay_frequency_stats(payroll_txs)
    
    # Should return zeros (can't calculate gaps with 1 paycheck)
    assert stats["median_pay_gap_days"] == 0.0
    assert stats["pay_gap_variability"] == 0.0


def test_compute_cashflow_buffer(in_memory_db, user_with_checking):
    """
    Test calculating cash-flow buffer in months.
    
    Why this test matters:
    - PRD Persona 2 criteria: cash-flow buffer < 1 month
    - Formula: checking balance / average monthly expenses
    - Shows financial runway without income
    """
    user, checking = user_with_checking
    
    # Checking balance is $1500
    # Create $1000/month in expenses
    for i in range(10):
        tx = Transaction(
            transaction_id=f"tx_expense_{i}",
            account_id=checking.account_id,
            amount=Decimal("100.00"),  # Total $1000
            transaction_date=date.today() - timedelta(days=i*3),
            merchant_name="Store",
            category="Shopping",
            transaction_type="debit"
        )
        in_memory_db.add(tx)
    
    in_memory_db.commit()
    
    signal = compute_income_signals("user_income_001", 30, in_memory_db)
    
    # Cash-flow buffer = $1500 / $1000 = 1.5 months
    assert abs(float(signal.cashflow_buffer_months) - 1.5) < 0.1


def test_compute_cashflow_buffer_zero_expenses(in_memory_db, user_with_checking):
    """
    Test cash-flow buffer with zero expenses (division by zero case).
    
    Why this test matters:
    - Edge case: brand new account with no activity
    - Should return 0, not crash with ZeroDivisionError
    """
    signal = compute_income_signals("user_income_001", 30, in_memory_db)
    
    # No expenses created, so buffer should be 0
    assert signal.cashflow_buffer_months == Decimal("0.00")


def test_compute_income_signals_no_accounts(in_memory_db):
    """
    Test computing income signals when user has no accounts.
    
    Why this test matters:
    - Edge case: completely new user
    - Should return zeros gracefully
    """
    user = User(user_id="user_no_accounts", email_masked="test@example.com")
    in_memory_db.add(user)
    in_memory_db.commit()
    
    signal = compute_income_signals("user_no_accounts", 30, in_memory_db)
    
    assert signal.payroll_deposit_count == 0
    assert signal.median_pay_gap_days == Decimal("0.00")
    assert signal.pay_gap_variability == Decimal("0.00")
    assert signal.avg_payroll_amount == Decimal("0.00")
    assert signal.cashflow_buffer_months == Decimal("0.00")


def test_compute_income_signals_meets_persona_criteria(in_memory_db, user_with_checking):
    """
    Test that signals meet Variable Income Budgeter persona criteria.
    
    Why this test matters:
    - Validates integration with persona assignment
    - PRD Persona 2: median pay gap > 45 days AND buffer < 1 month
    """
    user, checking = user_with_checking
    
    # Update checking balance to $500 (low buffer)
    checking.balance_current = Decimal("500.00")
    
    # Create irregular payroll: 60-day gaps
    paycheck_dates = [
        date.today(),
        date.today() - timedelta(days=60),
        date.today() - timedelta(days=120)
    ]
    
    for i, paycheck_date in enumerate(paycheck_dates):
        tx = Transaction(
            transaction_id=f"tx_payroll_{i}",
            account_id=checking.account_id,
            amount=Decimal("-2000.00"),
            transaction_date=paycheck_date,
            merchant_name="Payroll",
            category="Income",
            subcategory="Paycheck",
            transaction_type="credit"
        )
        in_memory_db.add(tx)
    
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
    
    signal = compute_income_signals("user_income_001", 120, in_memory_db)
    
    # Should meet Variable Income Budgeter criteria
    assert signal.median_pay_gap_days > Decimal("45.00")  # Criterion 1
    # Buffer = $500 / ($1000/month * 4) = 0.5 months < 1
    assert signal.cashflow_buffer_months < Decimal("1.00")  # Criterion 2


def test_compute_income_signals_stable_income(in_memory_db, user_with_checking):
    """
    Test income signals for stable, regular income (NOT Variable Income persona).
    
    Why this test matters:
    - Validates signals for users with stable income
    - Regular paychecks + good buffer = NOT Variable Income Budgeter
    """
    user, checking = user_with_checking
    
    # Good checking balance ($3000)
    checking.balance_current = Decimal("3000.00")
    
    # Create regular bi-weekly paychecks (14 days apart)
    for i in range(5):
        tx = Transaction(
            transaction_id=f"tx_payroll_{i}",
            account_id=checking.account_id,
            amount=Decimal("-2500.00"),
            transaction_date=date.today() - timedelta(days=i*14),
            merchant_name="Payroll",
            category="Income",
            subcategory="Paycheck",
            transaction_type="credit"
        )
        in_memory_db.add(tx)
    
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
    
    signal = compute_income_signals("user_income_001", 60, in_memory_db)
    
    # Should NOT meet Variable Income Budgeter criteria
    assert signal.median_pay_gap_days < Decimal("45.00")  # Regular income
    assert signal.cashflow_buffer_months > Decimal("1.00")  # Good buffer
    # Low variability indicates stable income
    assert signal.pay_gap_variability < Decimal("5.00")

