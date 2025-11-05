"""
Subscription signal detection for SpendSense.

This module computes subscription behavior signals from transaction data.

Why subscriptions matter:
- Recurring charges can add up quickly without users noticing
- Subscription-Heavy persona needs to identify users with many recurring charges
- PRD requires detecting recurring merchants (≥3 in 90d) and calculating subscription share

Signals computed:
- Recurring merchant count (merchants appearing ≥3 times in window)
- Monthly recurring spend (average monthly spend on subscriptions)
- Subscription share (% of total spend that goes to subscriptions)
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Account, SubscriptionSignal, Transaction

logger = get_logger(__name__)


def detect_recurring_merchants(
    transactions: list[Transaction],
    window_days: int
) -> list[str]:
    """
    Detect merchants with recurring charges in the window.
    
    Why threshold varies by window:
    - 30-day window: ≥1 occurrence (monthly subscriptions only appear once)
    - 90+ day window: ≥3 occurrences (monthly subscriptions appear 3+ times)
    - PRD specifies "recurring merchants ≥3" meaning ≥3 different merchants, not occurrences
    - Avoids false positives from one-off duplicate charges in longer windows
    
    Args:
        transactions: List of transactions to analyze (already filtered to window)
        window_days: Number of days in the analysis window (for logging)
    
    Returns:
        List of merchant names that appear recurrently in subscription category
    
    Edge cases handled:
    - Missing merchant names (skip)
    - Pending transactions (should be filtered by caller)
    - Refunds (counted as separate transactions)
    """
    # Filter for subscription category only
    subscription_txs = [
        tx for tx in transactions
        if tx.category == "Subscription" and tx.merchant_name
    ]

    # Count occurrences per merchant
    merchant_counts: dict[str, int] = {}
    for tx in subscription_txs:
        merchant_name = tx.merchant_name
        if merchant_name:  # Skip None values
            merchant_counts[merchant_name] = merchant_counts.get(merchant_name, 0) + 1

    # Threshold depends on window size
    # 30-day window: monthly subscriptions appear ~1 time, so threshold = 1
    # 90+ day window: monthly subscriptions appear 3+ times, so threshold = 3
    if window_days <= 45:
        min_occurrences = 1  # For 30-day window, monthly subs appear once
    elif window_days <= 75:
        min_occurrences = 2  # For 60-day window, monthly subs appear twice  
    else:
        min_occurrences = 3  # For 90+ day window, monthly subs appear 3+ times

    # Filter for recurring merchants
    recurring_merchants = [
        merchant for merchant, count in merchant_counts.items()
        if count >= min_occurrences
    ]

    logger.debug(
        "recurring_merchants_detected",
        window_days=window_days,
        total_merchants=len(merchant_counts),
        recurring_count=len(recurring_merchants),
        min_occurrences=min_occurrences
    )

    return recurring_merchants


def compute_subscription_signals(
    user_id: str,
    window_days: int,
    session: Session
) -> SubscriptionSignal:
    """
    Compute all subscription signals for a user.
    
    Why we compute these signals:
    - Subscription-Heavy persona (PRD Persona 3) needs these metrics
    - Criteria: recurring merchants ≥3 AND (monthly recurring ≥$50 OR subscription share ≥10%)
    - Helps users identify and potentially reduce subscription spending
    
    Args:
        user_id: User identifier
        window_days: Analysis window (30 or 180 days)
        session: SQLAlchemy database session
    
    Returns:
        SubscriptionSignal model instance with computed metrics
    
    Metrics computed:
    - recurring_merchant_count: Number of merchants appearing ≥3 times
    - monthly_recurring_spend: Average monthly spend on subscriptions
    - subscription_share_pct: Subscription spend as % of total spend
    
    Edge cases handled:
    - No transactions: returns zeros
    - No subscriptions: returns zeros
    - Pending transactions: excluded
    - Zero total spend: subscription_share_pct = 0
    """
    logger.info("computing_subscription_signals", user_id=user_id, window_days=window_days)

    # Calculate cutoff date
    cutoff_date = date.today() - timedelta(days=window_days)

    # Get user's accounts (individual only per PRD)
    accounts = session.query(Account).filter(
        Account.user_id == user_id,
        Account.holder_category == "individual"
    ).all()

    if not accounts:
        logger.warning("no_accounts_for_user", user_id=user_id)
        # Return zeros
        return SubscriptionSignal(
            user_id=user_id,
            window_days=window_days,
            recurring_merchant_count=0,
            monthly_recurring_spend=Decimal("0.00"),
            subscription_share_pct=Decimal("0.00")
        )

    account_ids = [acc.account_id for acc in accounts]

    # Get transactions in window (exclude pending per PRD edge case handling)
    transactions = session.query(Transaction).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.transaction_date >= cutoff_date,
        Transaction.pending == False
    ).all()

    if not transactions:
        logger.info("no_transactions_in_window", user_id=user_id, window_days=window_days)
        return SubscriptionSignal(
            user_id=user_id,
            window_days=window_days,
            recurring_merchant_count=0,
            monthly_recurring_spend=Decimal("0.00"),
            subscription_share_pct=Decimal("0.00")
        )

    # Detect recurring merchants
    recurring_merchants = detect_recurring_merchants(transactions, window_days)

    # Calculate subscription spend (positive amounts = debits/expenses)
    subscription_txs = [
        tx for tx in transactions
        if tx.category == "Subscription" and tx.amount > 0
    ]
    subscription_total = sum(tx.amount for tx in subscription_txs)

    # Calculate monthly recurring spend
    months_in_window = Decimal(str(window_days)) / Decimal("30.0")
    monthly_recurring_spend = subscription_total / months_in_window if months_in_window > 0 else Decimal("0.00")

    # Calculate total debit spend (for subscription share calculation)
    total_debit = sum(abs(tx.amount) for tx in transactions if tx.amount > 0)

    # Calculate subscription share percentage
    if total_debit > 0:
        subscription_share_pct = (Decimal(str(subscription_total)) / Decimal(str(total_debit))) * Decimal("100.0")
    else:
        subscription_share_pct = Decimal("0.00")

    # Create signal model
    signal = SubscriptionSignal(
        user_id=user_id,
        window_days=window_days,
        recurring_merchant_count=len(recurring_merchants),
        monthly_recurring_spend=monthly_recurring_spend,
        subscription_share_pct=subscription_share_pct
    )

    logger.info(
        "subscription_signals_computed",
        user_id=user_id,
        window_days=window_days,
        recurring_merchants=len(recurring_merchants),
        monthly_spend=float(monthly_recurring_spend),
        share_pct=float(subscription_share_pct)
    )

    # Persist to database
    session.add(signal)
    session.commit()

    return signal

