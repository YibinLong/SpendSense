"""
Credit signal detection for SpendSense.

This module computes credit utilization and behavior signals from liability and transaction data.

Why credit signals matter:
- High Utilization persona (PRD Persona 1) is the highest priority persona
- Credit utilization is a key factor in credit scores and financial health
- PRD criteria: any card ≥50% utilization OR interest > 0 OR minimum-only OR overdue
- Flags at 30%, 50%, 80% help identify escalating risk levels

Signals computed:
- Credit utilization per card (balance / limit * 100)
- Utilization flags for 30%, 50%, 80% thresholds
- Interest charges detected in transactions
- Minimum-payment-only behavior
- Overdue status
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Account, Transaction, Liability, CreditSignal


logger = get_logger(__name__)


def compute_credit_utilization(
    liabilities: List[Liability],
    transactions: List[Transaction]
) -> Dict[str, Any]:
    """
    Calculate credit utilization stats and flags.
    
    Why utilization matters:
    - Utilization above 30% can impact credit scores
    - Utilization above 50% is a strong signal for High Utilization persona
    - Utilization above 80% indicates high financial stress
    
    How utilization is calculated:
    - Per card: (current balance / credit limit) * 100
    - We track max and average across all cards
    - Cards with zero or missing credit limits are skipped
    
    Args:
        liabilities: List of credit card liabilities
        transactions: List of transactions (for context, not used in this function)
    
    Returns:
        Dict with utilization metrics:
        - max_pct: Highest utilization across all cards
        - avg_pct: Average utilization across all cards
        - flag_30: True if any card ≥30%
        - flag_50: True if any card ≥50%
        - flag_80: True if any card ≥80%
        - utilizations: List of per-card utilization percentages
    
    Edge cases handled:
    - Zero credit limit: skip card (can't calculate utilization)
    - No credit cards: return zeros and False flags
    """
    utilizations = []
    
    for liab in liabilities:
        # Only calculate if we have a valid credit limit
        if liab.credit_limit and liab.credit_limit > 0:
            util_pct = (liab.current_balance / liab.credit_limit) * Decimal("100.0")
            utilizations.append(float(util_pct))
    
    if utilizations:
        max_pct = max(utilizations)
        avg_pct = sum(utilizations) / len(utilizations)
        flag_30 = any(u >= 30 for u in utilizations)
        flag_50 = any(u >= 50 for u in utilizations)
        flag_80 = any(u >= 80 for u in utilizations)
    else:
        max_pct = 0.0
        avg_pct = 0.0
        flag_30 = False
        flag_50 = False
        flag_80 = False
    
    return {
        "max_pct": max_pct,
        "avg_pct": avg_pct,
        "flag_30": flag_30,
        "flag_50": flag_50,
        "flag_80": flag_80,
        "utilizations": utilizations
    }


def check_credit_flags(
    liabilities: List[Liability],
    transactions: List[Transaction]
) -> Dict[str, bool]:
    """
    Check for interest charges, minimum payments, and overdue status.
    
    Why these flags matter:
    - Interest charges = user is carrying a balance (not paying in full)
    - Minimum-payment-only = user may be struggling financially
    - Overdue = immediate financial distress signal
    - All three are criteria for High Utilization persona (PRD Persona 1)
    
    How flags are detected:
    - has_interest_charges: Look for "Interest Charge" merchant in transactions
    - has_minimum_payment_only: Last payment ≈ minimum payment (within 10% tolerance)
    - is_overdue: Check liability.is_overdue flag
    
    Why 10% tolerance for minimum payment:
    - Accounts for small variations in payment amounts
    - User might pay $25.50 when minimum is $25.00
    - Avoids false negatives from rounding
    
    Args:
        liabilities: List of credit card liabilities
        transactions: List of transactions in the window
    
    Returns:
        Dict with boolean flags:
        - has_interest_charges: Any interest charges found
        - has_minimum_payment_only: Any card paid only minimum
        - is_overdue: Any card is overdue
    
    Edge cases handled:
    - Missing last payment data: skip minimum payment check
    - No transactions: has_interest_charges = False
    """
    has_interest_charges = False
    has_minimum_payment_only = False
    is_overdue = False
    
    for liab in liabilities:
        # Check for interest charges in transactions
        if liab.account_id:
            interest_txs = [
                tx for tx in transactions 
                if tx.account_id == liab.account_id 
                and tx.merchant_name == "Interest Charge"
            ]
            if interest_txs:
                has_interest_charges = True
        
        # Check for minimum-payment-only behavior
        # If last payment ≈ minimum payment (within 10%), user is paying minimum only
        if liab.last_payment_amount and liab.minimum_payment:
            # Payment is within 10% of minimum = minimum-only
            if liab.last_payment_amount <= liab.minimum_payment * Decimal("1.1"):
                has_minimum_payment_only = True
        
        # Check overdue status
        if liab.is_overdue:
            is_overdue = True
    
    return {
        "has_interest_charges": has_interest_charges,
        "has_minimum_payment_only": has_minimum_payment_only,
        "is_overdue": is_overdue
    }


def compute_credit_signals(
    user_id: str,
    window_days: int,
    session: Session
) -> CreditSignal:
    """
    Compute all credit signals for a user.
    
    Why we compute these signals:
    - High Utilization persona (PRD Persona 1) is highest priority
    - Criteria: any card ≥50% utilization OR interest > 0 OR minimum-only OR overdue
    - These signals directly drive persona assignment and recommendations
    
    Args:
        user_id: User identifier
        window_days: Analysis window (30 or 180 days)
        session: SQLAlchemy database session
    
    Returns:
        CreditSignal model instance with computed metrics
    
    Metrics computed:
    - credit_utilization_max_pct: Highest utilization across all cards
    - credit_utilization_avg_pct: Average utilization across all cards
    - credit_util_flag_30/50/80: Threshold flags
    - has_interest_charges: Interest detected in transactions
    - has_minimum_payment_only: User paying only minimum
    - is_overdue: Any card is overdue
    
    Edge cases handled:
    - No credit cards: return zeros and False flags
    - No transactions: has_interest_charges = False
    - Cards with zero limit: skipped from utilization calculation
    """
    logger.info("computing_credit_signals", user_id=user_id, window_days=window_days)
    
    # Calculate cutoff date
    cutoff_date = date.today() - timedelta(days=window_days)
    
    # Get user's credit card liabilities
    liabilities = session.query(Liability).filter(
        Liability.user_id == user_id,
        Liability.liability_type == "credit_card"
    ).all()
    
    if not liabilities:
        logger.info("no_credit_cards", user_id=user_id)
        return CreditSignal(
            user_id=user_id,
            window_days=window_days,
            credit_utilization_max_pct=Decimal("0.00"),
            credit_utilization_avg_pct=Decimal("0.00"),
            credit_util_flag_30=False,
            credit_util_flag_50=False,
            credit_util_flag_80=False,
            has_interest_charges=False,
            has_minimum_payment_only=False,
            is_overdue=False
        )
    
    # Get user's accounts for transaction lookup
    accounts = session.query(Account).filter(
        Account.user_id == user_id,
        Account.holder_category == "individual"
    ).all()
    
    if accounts:
        account_ids = [acc.account_id for acc in accounts]
        
        # Get transactions in window (exclude pending)
        transactions = session.query(Transaction).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.transaction_date >= cutoff_date,
            Transaction.pending == False
        ).all()
    else:
        transactions = []
    
    # Compute utilization stats
    utilization_stats = compute_credit_utilization(liabilities, transactions)
    
    # Check credit behavior flags
    credit_flags = check_credit_flags(liabilities, transactions)
    
    # Create signal model
    signal = CreditSignal(
        user_id=user_id,
        window_days=window_days,
        credit_utilization_max_pct=Decimal(str(utilization_stats["max_pct"])),
        credit_utilization_avg_pct=Decimal(str(utilization_stats["avg_pct"])),
        credit_util_flag_30=utilization_stats["flag_30"],
        credit_util_flag_50=utilization_stats["flag_50"],
        credit_util_flag_80=utilization_stats["flag_80"],
        has_interest_charges=credit_flags["has_interest_charges"],
        has_minimum_payment_only=credit_flags["has_minimum_payment_only"],
        is_overdue=credit_flags["is_overdue"]
    )
    
    logger.info(
        "credit_signals_computed",
        user_id=user_id,
        window_days=window_days,
        max_util=float(signal.credit_utilization_max_pct),
        avg_util=float(signal.credit_utilization_avg_pct),
        flag_50=signal.credit_util_flag_50,
        has_interest=signal.has_interest_charges,
        overdue=signal.is_overdue
    )
    
    return signal

