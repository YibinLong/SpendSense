"""
Parquet analytics export for SpendSense.

This module exports denormalized data and computed features to Parquet files.

Why Parquet:
- Fast columnar analytics (pandas/polars friendly)
- Efficient storage with compression
- Easy to query for persona assignment
- Pre-computed features speed up downstream processing

Outputs:
- transactions_denorm.parquet: Transactions joined with user/account info
- features_30d.parquet: Per-user aggregated features (30-day window)
- features_180d.parquet: Per-user aggregated features (180-day window)
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.db.session import get_session
from spendsense.app.db.models import User, Account, Transaction, Liability
from spendsense.app.features import subscriptions, savings, credit, income


logger = get_logger(__name__)


def export_transactions_denorm() -> str:
    """
    Export denormalized transactions to Parquet.
    
    Why denormalized:
    - Joins transactions with user and account info
    - No JOINs needed for analytics queries
    - One table for all transaction analysis
    
    Returns:
        Path to created Parquet file
    
    Columns:
    - transaction_id, transaction_date, amount, merchant_name, category, subcategory
    - account_id, account_type, account_subtype
    - user_id
    """
    logger.info("exporting_denormalized_transactions")
    
    with next(get_session()) as session:
        # Query all transactions with joined account and user info
        query = session.query(
            # Transaction fields
            Transaction.transaction_id,
            Transaction.transaction_date,
            Transaction.amount,
            Transaction.currency,
            Transaction.merchant_name,
            Transaction.category,
            Transaction.subcategory,
            Transaction.transaction_type,
            Transaction.pending,
            Transaction.payment_channel,
            # Account fields
            Transaction.account_id,
            Account.account_type,
            Account.account_subtype,
            Account.holder_category,
            # User fields
            Account.user_id
        ).join(
            Account, Transaction.account_id == Account.account_id
        ).filter(
            Account.holder_category == "individual"  # Filter business accounts per PRD
        )
        
        # Convert to DataFrame
        df = pd.read_sql(query.statement, session.bind)  # type: ignore[arg-type]
        
        logger.info("transactions_queried", count=len(df))
        
        # Export to Parquet
        output_path = Path(settings.parquet_dir) / "transactions_denorm.parquet"
        df.to_parquet(output_path, index=False, compression="snappy")
        
        logger.info("transactions_denorm_exported", path=str(output_path), rows=len(df))
        
        return str(output_path)


def compute_window_features(window_days: int) -> pd.DataFrame:
    """
    Compute per-user aggregated features for a time window.
    
    Why window-based features:
    - Personas compare 30d vs 180d behavior
    - Recent behavior (30d) shows current state
    - Longer window (180d) shows trends
    
    Why this is now simpler:
    - Feature computation logic extracted to dedicated modules
    - Each module (subscriptions, savings, credit, income) is independently testable
    - This function now orchestrates the feature modules
    - Separation of concerns makes maintenance easier
    
    Args:
        window_days: Number of days to look back (30 or 180)
    
    Returns:
        DataFrame with one row per user, columns for all features
    
    Features computed (per PRD personas):
    - Subscriptions: recurring merchant count, monthly recurring spend, subscription share
    - Savings: net inflow to savings accounts, growth rate, emergency fund coverage
    - Credit: utilization per card, flags for 30%/50%/80%, minimum-payment-only, interest charges
    - Income: payroll frequency, variability, cash-flow buffer
    """
    logger.info("computing_window_features", window_days=window_days)
    
    cutoff_date = date.today() - timedelta(days=window_days)
    
    with next(get_session()) as session:
        # Get all users
        users = session.query(User).all()
        
        features_list = []
        
        for user in users:
            logger.debug("computing_features_for_user", user_id=user.user_id, window_days=window_days)
            
            # Check if user has accounts
            accounts = session.query(Account).filter(
                Account.user_id == user.user_id,
                Account.holder_category == "individual"
            ).all()
            
            if not accounts:
                logger.warning("no_accounts_for_user", user_id=user.user_id)
                continue
            
            # Initialize feature dict with metadata
            features: Dict[str, Any] = {
                "user_id": user.user_id,
                "window_days": window_days,
                "computed_at": pd.Timestamp.now()
            }
            
            # === COMPUTE SIGNALS USING FEATURE MODULES ===
            # This is the refactored approach - each signal type has its own module
            
            # Subscription signals
            subscription_signal = subscriptions.compute_subscription_signals(
                user.user_id, window_days, session
            )
            features["recurring_merchant_count"] = subscription_signal.recurring_merchant_count
            features["monthly_recurring_spend"] = float(subscription_signal.monthly_recurring_spend)
            features["subscription_share_pct"] = float(subscription_signal.subscription_share_pct)
            
            # Savings signals
            savings_signal = savings.compute_savings_signals(
                user.user_id, window_days, session
            )
            features["savings_net_inflow"] = float(savings_signal.savings_net_inflow)
            features["savings_growth_rate_pct"] = float(savings_signal.savings_growth_rate_pct)
            features["emergency_fund_months"] = float(savings_signal.emergency_fund_months)
            
            # Credit signals
            credit_signal = credit.compute_credit_signals(
                user.user_id, window_days, session
            )
            features["credit_utilization_max_pct"] = float(credit_signal.credit_utilization_max_pct)
            features["credit_utilization_avg_pct"] = float(credit_signal.credit_utilization_avg_pct)
            features["credit_util_flag_30"] = credit_signal.credit_util_flag_30
            features["credit_util_flag_50"] = credit_signal.credit_util_flag_50
            features["credit_util_flag_80"] = credit_signal.credit_util_flag_80
            features["has_interest_charges"] = credit_signal.has_interest_charges
            features["has_minimum_payment_only"] = credit_signal.has_minimum_payment_only
            features["is_overdue"] = credit_signal.is_overdue
            
            # Income signals
            income_signal = income.compute_income_signals(
                user.user_id, window_days, session
            )
            features["payroll_deposit_count"] = income_signal.payroll_deposit_count
            features["median_pay_gap_days"] = float(income_signal.median_pay_gap_days)
            features["pay_gap_variability"] = float(income_signal.pay_gap_variability)
            features["avg_payroll_amount"] = float(income_signal.avg_payroll_amount)
            features["cashflow_buffer_months"] = float(income_signal.cashflow_buffer_months)
            
            # === GENERAL SPENDING METRICS ===
            # These are still computed here as they don't fit into a specific signal category
            account_ids = [acc.account_id for acc in accounts]
            transactions = session.query(Transaction).filter(
                Transaction.account_id.in_(account_ids),
                Transaction.transaction_date >= cutoff_date,
                Transaction.pending == False
            ).all()
            
            total_income = sum(abs(tx.amount) for tx in transactions if tx.amount < 0)  # Credits
            total_expenses = sum(tx.amount for tx in transactions if tx.amount > 0)  # Debits
            
            features["total_income"] = float(total_income)
            features["total_expenses"] = float(total_expenses)
            features["net_cashflow"] = float(total_income - total_expenses)
            
            features_list.append(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        
        logger.info("window_features_computed", window_days=window_days, users=len(df))
        
        return df


def export_features_to_parquet() -> Dict[str, str]:
    """
    Export all feature tables to Parquet.
    
    Why separate files:
    - 30d and 180d are different analyses
    - Easy to load just what you need
    - Clear naming convention
    
    Returns:
        Dict with paths to created files
    
    Outputs:
    - features_30d.parquet: 30-day window features
    - features_180d.parquet: 180-day window features
    """
    logger.info("exporting_features_to_parquet")
    
    paths = {}
    
    # 30-day features
    df_30d = compute_window_features(30)
    path_30d = Path(settings.parquet_dir) / "features_30d.parquet"
    df_30d.to_parquet(path_30d, index=False, compression="snappy")
    paths["30d"] = str(path_30d)
    logger.info("features_30d_exported", path=str(path_30d), rows=len(df_30d))
    
    # 180-day features
    df_180d = compute_window_features(180)
    path_180d = Path(settings.parquet_dir) / "features_180d.parquet"
    df_180d.to_parquet(path_180d, index=False, compression="snappy")
    paths["180d"] = str(path_180d)
    logger.info("features_180d_exported", path=str(path_180d), rows=len(df_180d))
    
    return paths


def export_all() -> Dict[str, Any]:
    """
    Export all analytics files to Parquet.
    
    Convenience function to export everything at once.
    
    Returns:
        Dict with all export paths and statistics
    
    Usage:
        from spendsense.app.db.parquet_export import export_all
        
        results = export_all()
        print(results)
    """
    logger.info("exporting_all_analytics")
    
    results = {
        "transactions_denorm": export_transactions_denorm(),
        "features": export_features_to_parquet()
    }
    
    logger.info("all_analytics_exported", results=results)
    
    return results

