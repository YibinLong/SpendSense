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
            
            # Get user's accounts (individual only)
            accounts = session.query(Account).filter(
                Account.user_id == user.user_id,
                Account.holder_category == "individual"
            ).all()
            
            if not accounts:
                logger.warning("no_accounts_for_user", user_id=user.user_id)
                continue
            
            account_ids = [acc.account_id for acc in accounts]
            
            # Get transactions in window
            transactions = session.query(Transaction).filter(
                Transaction.account_id.in_(account_ids),
                Transaction.transaction_date >= cutoff_date,
                Transaction.pending == False  # Exclude pending
            ).all()
            
            # Initialize feature dict
            features: Dict[str, Any] = {
                "user_id": user.user_id,
                "window_days": window_days,
                "computed_at": pd.Timestamp.now()
            }
            
            # === SUBSCRIPTION SIGNALS ===
            # Recurring merchants (≥3 occurrences with similar amounts monthly)
            subscription_candidates = [tx for tx in transactions if tx.category == "Subscription"]
            recurring_merchants = set()
            for merchant_name in set(tx.merchant_name for tx in subscription_candidates if tx.merchant_name):
                merchant_txs = [tx for tx in subscription_candidates if tx.merchant_name == merchant_name]
                if len(merchant_txs) >= 3:
                    recurring_merchants.add(merchant_name)
            
            features["recurring_merchant_count"] = len(recurring_merchants)
            
            # Monthly recurring spend (average monthly spend on subscriptions)
            subscription_total = sum(tx.amount for tx in subscription_candidates)
            months_in_window = window_days / 30.0
            features["monthly_recurring_spend"] = float(subscription_total / Decimal(str(months_in_window)))
            
            # Subscription share of total spend (debits only, positive amounts)
            total_debit = sum(abs(tx.amount) for tx in transactions if tx.amount > 0)
            features["subscription_share_pct"] = (
                (float(subscription_total / total_debit) * 100) if total_debit > 0 else 0.0
            )
            
            # === SAVINGS SIGNALS ===
            savings_accounts = [acc for acc in accounts if acc.account_subtype == "savings"]
            
            if savings_accounts:
                # Net inflow to savings (credits - debits)
                savings_account_ids = [acc.account_id for acc in savings_accounts]
                savings_txs = [tx for tx in transactions if tx.account_id in savings_account_ids]
                
                credits = sum(abs(tx.amount) for tx in savings_txs if tx.amount < 0)  # Credits are negative
                debits = sum(tx.amount for tx in savings_txs if tx.amount > 0)
                net_inflow = credits - debits
                
                features["savings_net_inflow"] = float(net_inflow)
                
                # Growth rate (current balance vs. N days ago estimate)
                current_savings_balance = sum(acc.balance_current for acc in savings_accounts)
                # Estimate past balance: current - net_inflow
                past_balance_estimate = current_savings_balance - net_inflow
                features["savings_growth_rate_pct"] = (
                    (float(net_inflow / past_balance_estimate) * 100) if past_balance_estimate > 0 else 0.0
                )
                
                # Emergency fund coverage (savings balance / avg monthly expenses)
                checking_txs = [tx for tx in transactions if any(
                    tx.account_id == acc.account_id for acc in accounts if acc.account_subtype == "checking"
                ) and tx.amount > 0]  # Debits only
                
                avg_monthly_expenses = sum(tx.amount for tx in checking_txs) / Decimal(str(months_in_window))
                features["emergency_fund_months"] = (
                    float(current_savings_balance / avg_monthly_expenses) if avg_monthly_expenses > 0 else 0.0
                )
            else:
                features["savings_net_inflow"] = 0.0
                features["savings_growth_rate_pct"] = 0.0
                features["emergency_fund_months"] = 0.0
            
            # === CREDIT SIGNALS ===
            liabilities = session.query(Liability).filter(
                Liability.user_id == user.user_id,
                Liability.liability_type == "credit_card"
            ).all()
            
            utilizations = []
            has_interest_charges = False
            has_minimum_payment_only = False
            has_overdue = False
            
            for liab in liabilities:
                if liab.credit_limit and liab.credit_limit > 0:
                    util = float((liab.current_balance / liab.credit_limit) * 100)
                    utilizations.append(util)
                
                # Check for interest charges in transactions
                if liab.account_id:
                    interest_txs = [tx for tx in transactions 
                                   if tx.account_id == liab.account_id 
                                   and tx.merchant_name == "Interest Charge"]
                    if interest_txs:
                        has_interest_charges = True
                
                # Minimum payment only (last payment ≈ minimum payment)
                if liab.last_payment_amount and liab.minimum_payment:
                    if liab.last_payment_amount <= liab.minimum_payment * Decimal("1.1"):  # Within 10%
                        has_minimum_payment_only = True
                
                if liab.is_overdue:
                    has_overdue = True
            
            # Utilization stats
            if utilizations:
                features["credit_utilization_max_pct"] = max(utilizations)
                features["credit_utilization_avg_pct"] = sum(utilizations) / len(utilizations)
                features["credit_util_flag_30"] = any(u >= 30 for u in utilizations)
                features["credit_util_flag_50"] = any(u >= 50 for u in utilizations)
                features["credit_util_flag_80"] = any(u >= 80 for u in utilizations)
            else:
                features["credit_utilization_max_pct"] = 0.0
                features["credit_utilization_avg_pct"] = 0.0
                features["credit_util_flag_30"] = False
                features["credit_util_flag_50"] = False
                features["credit_util_flag_80"] = False
            
            features["has_interest_charges"] = has_interest_charges
            features["has_minimum_payment_only"] = has_minimum_payment_only
            features["is_overdue"] = has_overdue
            
            # === INCOME STABILITY SIGNALS ===
            # Payroll deposits (negative amounts, category = Income)
            payroll_txs = [tx for tx in transactions 
                          if tx.category == "Income" 
                          and tx.subcategory == "Paycheck"
                          and tx.amount < 0]
            
            features["payroll_deposit_count"] = len(payroll_txs)
            
            if len(payroll_txs) >= 2:
                # Sort by date
                payroll_txs_sorted = sorted(payroll_txs, key=lambda x: x.transaction_date)
                
                # Calculate gaps between payrolls
                gaps = []
                for i in range(1, len(payroll_txs_sorted)):
                    gap_days = (payroll_txs_sorted[i].transaction_date - payroll_txs_sorted[i-1].transaction_date).days
                    gaps.append(gap_days)
                
                if gaps:
                    features["median_pay_gap_days"] = float(pd.Series(gaps).median())
                    features["pay_gap_variability"] = float(pd.Series(gaps).std())
                else:
                    features["median_pay_gap_days"] = 0.0
                    features["pay_gap_variability"] = 0.0
                
                # Average income amount
                avg_income = sum(abs(tx.amount) for tx in payroll_txs) / len(payroll_txs)
                features["avg_payroll_amount"] = float(avg_income)
            else:
                features["median_pay_gap_days"] = 0.0
                features["pay_gap_variability"] = 0.0
                features["avg_payroll_amount"] = 0.0
            
            # Cash-flow buffer (checking balance / avg monthly expenses)
            checking_accounts = [acc for acc in accounts if acc.account_subtype == "checking"]
            if checking_accounts:
                checking_balance = sum(acc.balance_current for acc in checking_accounts)
                
                checking_txs = [tx for tx in transactions if any(
                    tx.account_id == acc.account_id for acc in checking_accounts
                ) and tx.amount > 0]  # Debits only
                
                avg_monthly_expenses = sum(tx.amount for tx in checking_txs) / Decimal(str(months_in_window))
                features["cashflow_buffer_months"] = (
                    float(checking_balance / avg_monthly_expenses) if avg_monthly_expenses > 0 else 0.0
                )
            else:
                features["cashflow_buffer_months"] = 0.0
            
            # === GENERAL SPENDING METRICS ===
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

