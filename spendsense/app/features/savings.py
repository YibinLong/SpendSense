"""
Savings signal detection for SpendSense.

This module computes savings behavior signals from account and transaction data.

Why savings signals matter:
- Savings Builder persona (PRD Persona 4) needs these metrics
- Emergency fund coverage is a critical financial health indicator
- Growth rate shows positive financial trends
- PRD criteria: savings growth ≥2% OR net inflow ≥$200/month AND utilization < 30%

Signals computed:
- Net inflow to savings accounts (credits - debits)
- Savings growth rate percentage
- Emergency fund coverage (months of expenses covered by savings)
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Account, Transaction, SavingsSignal


logger = get_logger(__name__)


def compute_savings_signals(
    user_id: str,
    window_days: int,
    session: Session
) -> SavingsSignal:
    """
    Compute savings signals for a user.
    
    Why we compute these signals:
    - Savings Builder persona needs to identify users building emergency funds
    - Emergency fund coverage (savings / monthly expenses) is a standard financial metric
    - Growth rate shows if user is making progress toward savings goals
    
    Args:
        user_id: User identifier
        window_days: Analysis window (30 or 180 days)
        session: SQLAlchemy database session
    
    Returns:
        SavingsSignal model instance with computed metrics
    
    Metrics computed:
    - savings_net_inflow: Net amount deposited to savings (credits - debits)
    - savings_growth_rate_pct: Growth percentage based on net inflow
    - emergency_fund_months: Current savings balance / average monthly expenses
    
    How growth rate works:
    - Current savings balance = starting balance + net inflow
    - Growth rate = (net inflow / starting balance) * 100
    - Example: If you had $1000 and saved $50, growth = 5%
    
    How emergency fund coverage works:
    - Standard financial advice: 3-6 months of expenses in savings
    - Formula: current savings balance / average monthly expenses
    - Example: $3000 savings / $1000 monthly expenses = 3 months coverage
    
    Edge cases handled:
    - No savings account: returns zeros
    - No expenses (division by zero): emergency_fund_months = 0
    - Negative growth (spending from savings): allowed, shows depletion
    """
    logger.info("computing_savings_signals", user_id=user_id, window_days=window_days)
    
    # Calculate cutoff date
    cutoff_date = date.today() - timedelta(days=window_days)
    
    # Get user's accounts (individual only per PRD)
    accounts = session.query(Account).filter(
        Account.user_id == user_id,
        Account.holder_category == "individual"
    ).all()
    
    if not accounts:
        logger.warning("no_accounts_for_user", user_id=user_id)
        return SavingsSignal(
            user_id=user_id,
            window_days=window_days,
            savings_net_inflow=Decimal("0.00"),
            savings_growth_rate_pct=Decimal("0.00"),
            emergency_fund_months=Decimal("0.00")
        )
    
    # Filter for savings accounts
    savings_accounts = [acc for acc in accounts if acc.account_subtype == "savings"]
    
    if not savings_accounts:
        logger.info("no_savings_account", user_id=user_id)
        return SavingsSignal(
            user_id=user_id,
            window_days=window_days,
            savings_net_inflow=Decimal("0.00"),
            savings_growth_rate_pct=Decimal("0.00"),
            emergency_fund_months=Decimal("0.00")
        )
    
    account_ids = [acc.account_id for acc in accounts]
    savings_account_ids = [acc.account_id for acc in savings_accounts]
    
    # Get all transactions in window (exclude pending)
    transactions = session.query(Transaction).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= cutoff_date,
        Transaction.pending == False
    ).all()
    
    # Get savings transactions
    savings_txs = [tx for tx in transactions if tx.account_id in savings_account_ids]
    
    # Calculate net inflow to savings
    # In Plaid-style data: credits (deposits) are negative, debits (withdrawals) are positive
    credits = sum(abs(tx.amount) for tx in savings_txs if tx.amount < 0)
    debits = sum(tx.amount for tx in savings_txs if tx.amount > 0)
    net_inflow = credits - debits
    
    # Calculate current savings balance
    current_savings_balance = sum(acc.balance_current for acc in savings_accounts)
    
    # Calculate growth rate
    # Past balance estimate = current balance - net inflow
    past_balance_estimate = current_savings_balance - net_inflow
    
    if past_balance_estimate > 0:
        savings_growth_rate_pct = (Decimal(str(net_inflow)) / Decimal(str(past_balance_estimate))) * Decimal("100.0")
    else:
        # If past balance was zero or negative, can't calculate meaningful growth rate
        savings_growth_rate_pct = Decimal("0.00")
    
    # Calculate emergency fund coverage
    # Get checking account transactions for expense calculation
    checking_txs = [
        tx for tx in transactions 
        if any(tx.account_id == acc.account_id for acc in accounts if acc.account_subtype == "checking")
        and tx.amount > 0  # Debits only (expenses)
    ]
    
    # Calculate average monthly expenses
    months_in_window = Decimal(str(window_days)) / Decimal("30.0")
    total_expenses = sum(tx.amount for tx in checking_txs)
    avg_monthly_expenses = total_expenses / months_in_window if months_in_window > 0 else Decimal("0.00")
    
    # Calculate emergency fund months
    if avg_monthly_expenses > 0:
        emergency_fund_months = current_savings_balance / avg_monthly_expenses
    else:
        # No expenses tracked means we can't calculate coverage
        emergency_fund_months = Decimal("0.00")
    
    # Create signal model
    signal = SavingsSignal(
        user_id=user_id,
        window_days=window_days,
        savings_net_inflow=net_inflow,
        savings_growth_rate_pct=savings_growth_rate_pct,
        emergency_fund_months=emergency_fund_months
    )
    
    logger.info(
        "savings_signals_computed",
        user_id=user_id,
        window_days=window_days,
        net_inflow=float(net_inflow),
        growth_rate_pct=float(savings_growth_rate_pct),
        emergency_fund_months=float(emergency_fund_months)
    )
    
    return signal

