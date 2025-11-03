"""
Income stability signal detection for SpendSense.

This module computes income stability signals from transaction and account data.

Why income signals matter:
- Variable Income Budgeter persona (PRD Persona 2) targets users with irregular income
- PRD criteria: median pay gap > 45 days AND cash-flow buffer < 1 month
- Income variability affects budgeting strategies and financial planning
- Cash-flow buffer shows how long user can survive without income

Signals computed:
- Payroll deposit count
- Median pay gap (days between paychecks)
- Pay gap variability (standard deviation)
- Average payroll amount
- Cash-flow buffer (checking balance / monthly expenses)
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict

from sqlalchemy.orm import Session
import pandas as pd

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Account, Transaction, IncomeSignal


logger = get_logger(__name__)


def detect_payroll_transactions(
    transactions: List[Transaction]
) -> List[Transaction]:
    """
    Filter for payroll deposit transactions.
    
    Why we detect payroll specifically:
    - Distinguishes regular employment income from one-off transfers
    - Enables frequency and variability analysis
    - Foundation for Variable Income Budgeter persona
    
    Payroll detection criteria (Plaid-style):
    - category = "Income"
    - subcategory = "Paycheck"
    - amount < 0 (credits are negative in Plaid convention)
    
    Args:
        transactions: List of all transactions to filter
    
    Returns:
        List of payroll transactions only
    
    Edge cases handled:
    - Non-payroll income (dividends, tax refunds): excluded
    - Pending transactions: should be filtered by caller
    """
    payroll_txs = [
        tx for tx in transactions
        if tx.category == "Income"
        and tx.subcategory == "Paycheck"
        and tx.amount < 0  # Credits are negative
    ]
    
    logger.debug("payroll_transactions_detected", count=len(payroll_txs))
    
    return payroll_txs


def compute_pay_frequency_stats(
    payroll_txs: List[Transaction]
) -> Dict[str, float]:
    """
    Calculate pay gap median and variability.
    
    Why median and not average:
    - Median is robust to outliers (e.g., missed paycheck, vacation)
    - Handles bi-weekly (14 days), semi-monthly (15 days), monthly (30 days) patterns
    - Standard deviation shows consistency vs. irregularity
    
    How it works:
    - Sort paychecks by date
    - Calculate days between consecutive paychecks
    - Median = middle value (50th percentile)
    - Variability = standard deviation of gaps
    
    Example:
    - Bi-weekly: gaps = [14, 14, 14, 14] → median = 14, variability = 0
    - Irregular: gaps = [7, 21, 14, 28] → median = 17.5, variability = high
    
    Args:
        payroll_txs: List of payroll transactions (should be ≥2 for meaningful stats)
    
    Returns:
        Dict with:
        - median_pay_gap_days: Median days between paychecks
        - pay_gap_variability: Standard deviation of pay gaps
        - avg_payroll_amount: Average paycheck amount
    
    Edge cases handled:
    - < 2 paychecks: return zeros (can't calculate gaps)
    - Single paycheck: return zeros
    """
    if len(payroll_txs) < 2:
        return {
            "median_pay_gap_days": 0.0,
            "pay_gap_variability": 0.0,
            "avg_payroll_amount": 0.0
        }
    
    # Sort by date
    payroll_txs_sorted = sorted(payroll_txs, key=lambda x: x.transaction_date)
    
    # Calculate gaps between consecutive paychecks
    gaps = []
    for i in range(1, len(payroll_txs_sorted)):
        gap_days = (payroll_txs_sorted[i].transaction_date - payroll_txs_sorted[i-1].transaction_date).days
        gaps.append(gap_days)
    
    # Calculate median and variability using pandas
    if gaps:
        median_gap = float(pd.Series(gaps).median())
        variability = float(pd.Series(gaps).std())
    else:
        median_gap = 0.0
        variability = 0.0
    
    # Calculate average payroll amount (absolute value since they're negative)
    avg_amount = sum(abs(tx.amount) for tx in payroll_txs) / len(payroll_txs)
    
    return {
        "median_pay_gap_days": median_gap,
        "pay_gap_variability": variability,
        "avg_payroll_amount": float(avg_amount)
    }


def compute_income_signals(
    user_id: str,
    window_days: int,
    session: Session
) -> IncomeSignal:
    """
    Compute income stability signals for a user.
    
    Why we compute these signals:
    - Variable Income Budgeter persona needs irregular income detection
    - PRD criteria: median pay gap > 45 days AND cash-flow buffer < 1 month
    - Cash-flow buffer shows financial runway without income
    
    Args:
        user_id: User identifier
        window_days: Analysis window (30 or 180 days)
        session: SQLAlchemy database session
    
    Returns:
        IncomeSignal model instance with computed metrics
    
    Metrics computed:
    - payroll_deposit_count: Number of paychecks in window
    - median_pay_gap_days: Median days between paychecks
    - pay_gap_variability: Standard deviation of pay gaps
    - avg_payroll_amount: Average paycheck amount
    - cashflow_buffer_months: Checking balance / avg monthly expenses
    
    Cash-flow buffer explained:
    - How many months can user survive on checking balance alone?
    - Formula: checking balance / average monthly expenses
    - Example: $2000 checking / $1000 monthly expenses = 2 months buffer
    - < 1 month buffer is a criterion for Variable Income Budgeter persona
    
    Edge cases handled:
    - No paychecks: return zeros
    - < 2 paychecks: can't calculate gaps (return zeros)
    - No expenses: cashflow_buffer = 0 (can't calculate without expenses)
    """
    logger.info("computing_income_signals", user_id=user_id, window_days=window_days)
    
    # Calculate cutoff date
    cutoff_date = date.today() - timedelta(days=window_days)
    
    # Get user's accounts (individual only per PRD)
    accounts = session.query(Account).filter(
        Account.user_id == user_id,
        Account.holder_category == "individual"
    ).all()
    
    if not accounts:
        logger.warning("no_accounts_for_user", user_id=user_id)
        return IncomeSignal(
            user_id=user_id,
            window_days=window_days,
            payroll_deposit_count=0,
            median_pay_gap_days=Decimal("0.00"),
            pay_gap_variability=Decimal("0.00"),
            avg_payroll_amount=Decimal("0.00"),
            cashflow_buffer_months=Decimal("0.00")
        )
    
    account_ids = [acc.account_id for acc in accounts]
    
    # Get transactions in window (exclude pending)
    transactions = session.query(Transaction).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= cutoff_date,
        Transaction.pending == False
    ).all()
    
    # Detect payroll transactions
    payroll_txs = detect_payroll_transactions(transactions)
    
    # Compute pay frequency stats
    frequency_stats = compute_pay_frequency_stats(payroll_txs)
    
    # Calculate cash-flow buffer
    # Get checking accounts
    checking_accounts = [acc for acc in accounts if acc.account_subtype == "checking"]
    
    if checking_accounts:
        checking_balance = sum(acc.balance_current for acc in checking_accounts)
        
        # Get checking account expenses (debits only)
        checking_txs = [
            tx for tx in transactions
            if any(tx.account_id == acc.account_id for acc in checking_accounts)
            and tx.amount > 0  # Debits only (expenses)
        ]
        
        # Calculate average monthly expenses
        months_in_window = Decimal(str(window_days / 30.0))
        total_expenses = sum(tx.amount for tx in checking_txs)
        avg_monthly_expenses = total_expenses / months_in_window if months_in_window > 0 else Decimal("0.00")
        
        # Calculate buffer
        if avg_monthly_expenses > 0:
            cashflow_buffer_months = checking_balance / avg_monthly_expenses
        else:
            cashflow_buffer_months = Decimal("0.00")
    else:
        cashflow_buffer_months = Decimal("0.00")
    
    # Create signal model
    signal = IncomeSignal(
        user_id=user_id,
        window_days=window_days,
        payroll_deposit_count=len(payroll_txs),
        median_pay_gap_days=Decimal(str(frequency_stats["median_pay_gap_days"])),
        pay_gap_variability=Decimal(str(frequency_stats["pay_gap_variability"])),
        avg_payroll_amount=Decimal(str(frequency_stats["avg_payroll_amount"])),
        cashflow_buffer_months=cashflow_buffer_months
    )
    
    logger.info(
        "income_signals_computed",
        user_id=user_id,
        window_days=window_days,
        payroll_count=len(payroll_txs),
        median_gap=float(signal.median_pay_gap_days),
        buffer_months=float(signal.cashflow_buffer_months)
    )
    
    return signal

