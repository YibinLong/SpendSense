"""
Persona criteria rules for SpendSense.

This module defines the 5 personas from the PRD with their exact criteria.
Each persona has a check function that evaluates signals and returns whether
the criteria are met, plus a dict explaining which conditions triggered.

Personas (in priority order):
1. High Utilization - Any card ≥50% OR interest > 0 OR minimum-only OR overdue
2. Variable Income Budgeter - Median pay gap > 45 days AND cash-flow buffer < 1 month
3. Subscription-Heavy - Recurring merchants ≥3 AND (monthly recurring ≥$50 OR subscription share ≥10%)
4. Savings Builder - Savings growth ≥2% OR net inflow ≥$200/mo AND all card utilizations < 30%
5. Cash-Flow Optimizer - Avg monthly expenses > income by 5-15%, stable income, utilization < 50%

Why priority order matters:
- High utilization is highest risk → highest priority
- Deterministic assignment when multiple personas match
- First match wins, no ties
"""

from decimal import Decimal
from typing import Optional, Tuple, Dict, Any

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    SubscriptionSignal,
    SavingsSignal,
    CreditSignal,
    IncomeSignal,
)


logger = get_logger(__name__)


def check_high_utilization(
    credit: Optional[CreditSignal],
    subscription: Optional[SubscriptionSignal],
    savings: Optional[SavingsSignal],
    income: Optional[IncomeSignal],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Persona 1: High Utilization (Priority 1 - Highest).
    
    Criteria (ANY of these):
    - Any card utilization ≥ 50%
    - Interest charges present
    - Minimum payment only behavior
    - Overdue payments
    
    Why this is priority 1:
    - Highest financial risk
    - Immediate action needed to avoid debt spiral
    - PRD specifies this as most critical persona
    
    Args:
        credit: Credit signal data (can be None if not computed)
        subscription: Subscription signal data (not used for this persona)
        savings: Savings signal data (not used for this persona)
        income: Income signal data (not used for this persona)
    
    Returns:
        Tuple of (matches: bool, criteria_met: dict)
        
    Example criteria_met:
        {
            "persona": "high_utilization",
            "credit_utilization_max_pct": 68.5,
            "credit_util_flag_50": true,
            "has_interest_charges": true,
            "has_minimum_payment_only": false,
            "is_overdue": false,
            "matched_on": ["credit_util_flag_50", "has_interest_charges"]
        }
    """
    if not credit:
        return False, {}
    
    criteria_met: Dict[str, Any] = {
        "persona": "high_utilization",
        "credit_utilization_max_pct": float(credit.credit_utilization_max_pct),
        "credit_util_flag_50": credit.credit_util_flag_50,
        "has_interest_charges": credit.has_interest_charges,
        "has_minimum_payment_only": credit.has_minimum_payment_only,
        "is_overdue": credit.is_overdue,
        "matched_on": [],
    }
    
    # Check all conditions
    if credit.credit_util_flag_50:
        criteria_met["matched_on"].append("credit_util_flag_50")
    if credit.has_interest_charges:
        criteria_met["matched_on"].append("has_interest_charges")
    if credit.has_minimum_payment_only:
        criteria_met["matched_on"].append("has_minimum_payment_only")
    if credit.is_overdue:
        criteria_met["matched_on"].append("is_overdue")
    
    # Match if ANY condition is true
    matches = len(criteria_met["matched_on"]) > 0
    
    return matches, criteria_met


def check_variable_income_budgeter(
    credit: Optional[CreditSignal],
    subscription: Optional[SubscriptionSignal],
    savings: Optional[SavingsSignal],
    income: Optional[IncomeSignal],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Persona 2: Variable Income Budgeter (Priority 2).
    
    Criteria (ALL of these):
    - Median pay gap > 45 days
    - Cash-flow buffer < 1 month
    
    Why this persona:
    - Irregular income makes budgeting challenging
    - Low buffer means immediate cash-flow stress
    - Needs percent-based budgeting and emergency fund
    
    Returns:
        Tuple of (matches: bool, criteria_met: dict)
    """
    if not income:
        return False, {}
    
    criteria_met: Dict[str, Any] = {
        "persona": "variable_income_budgeter",
        "median_pay_gap_days": float(income.median_pay_gap_days),
        "cashflow_buffer_months": float(income.cashflow_buffer_months),
        "matched_on": [],
    }
    
    # Check both conditions
    pay_gap_high = income.median_pay_gap_days > Decimal("45")
    buffer_low = income.cashflow_buffer_months < Decimal("1")
    
    if pay_gap_high:
        criteria_met["matched_on"].append("median_pay_gap_above_45_days")
    if buffer_low:
        criteria_met["matched_on"].append("cashflow_buffer_below_1_month")
    
    # Match only if BOTH conditions are true
    matches = pay_gap_high and buffer_low
    
    return matches, criteria_met


def check_subscription_heavy(
    credit: Optional[CreditSignal],
    subscription: Optional[SubscriptionSignal],
    savings: Optional[SavingsSignal],
    income: Optional[IncomeSignal],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Persona 3: Subscription-Heavy (Priority 3).
    
    Criteria (ALL of these):
    - Recurring merchants ≥ 3
    - Monthly recurring spend ≥ $50 (30d window) OR subscription share ≥ 10%
    
    Why this persona:
    - Many subscriptions create "subscription creep"
    - Often forgotten or underutilized services
    - Quick wins from auditing and canceling
    
    Returns:
        Tuple of (matches: bool, criteria_met: dict)
    """
    if not subscription:
        return False, {}
    
    criteria_met: Dict[str, Any] = {
        "persona": "subscription_heavy",
        "recurring_merchant_count": subscription.recurring_merchant_count,
        "monthly_recurring_spend": float(subscription.monthly_recurring_spend),
        "subscription_share_pct": float(subscription.subscription_share_pct),
        "matched_on": [],
    }
    
    # Check conditions
    has_multiple_subs = subscription.recurring_merchant_count >= 3
    spend_high = subscription.monthly_recurring_spend >= Decimal("50")
    share_high = subscription.subscription_share_pct >= Decimal("10")
    
    if has_multiple_subs:
        criteria_met["matched_on"].append("recurring_merchants_gte_3")
    if spend_high:
        criteria_met["matched_on"].append("monthly_recurring_gte_50")
    if share_high:
        criteria_met["matched_on"].append("subscription_share_gte_10_pct")
    
    # Match if: has ≥3 merchants AND (high spend OR high share)
    matches = has_multiple_subs and (spend_high or share_high)
    
    return matches, criteria_met


def check_savings_builder(
    credit: Optional[CreditSignal],
    subscription: Optional[SubscriptionSignal],
    savings: Optional[SavingsSignal],
    income: Optional[IncomeSignal],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Persona 4: Savings Builder (Priority 4).
    
    Criteria:
    - (Savings growth ≥ 2% over window OR net savings inflow ≥ $200/month)
    - AND all card utilizations < 30%
    
    Why this persona:
    - Positive savings behavior to reinforce
    - Low credit utilization shows financial stability
    - Focus: goal setting, automation, APY optimization
    
    Returns:
        Tuple of (matches: bool, criteria_met: dict)
    """
    if not savings:
        return False, {}
    
    criteria_met: Dict[str, Any] = {
        "persona": "savings_builder",
        "savings_growth_rate_pct": float(savings.savings_growth_rate_pct),
        "savings_net_inflow": float(savings.savings_net_inflow),
        "matched_on": [],
    }
    
    # Check savings conditions
    growth_positive = savings.savings_growth_rate_pct >= Decimal("2")
    inflow_positive = savings.savings_net_inflow >= Decimal("200")
    
    if growth_positive:
        criteria_met["matched_on"].append("savings_growth_gte_2_pct")
    if inflow_positive:
        criteria_met["matched_on"].append("net_inflow_gte_200_per_month")
    
    # Check credit utilization (must be low)
    credit_low = True
    if credit:
        credit_low = not credit.credit_util_flag_30
        criteria_met["credit_utilization_max_pct"] = float(credit.credit_utilization_max_pct)
        criteria_met["credit_util_flag_30"] = credit.credit_util_flag_30
        if credit_low:
            criteria_met["matched_on"].append("all_cards_below_30_pct")
    else:
        # If no credit data, assume low utilization
        criteria_met["credit_utilization_max_pct"] = 0.0
        criteria_met["credit_util_flag_30"] = False
        criteria_met["matched_on"].append("no_credit_cards")
    
    # Match if: (growth OR inflow) AND low credit utilization
    matches = (growth_positive or inflow_positive) and credit_low
    
    return matches, criteria_met


def check_cash_flow_optimizer(
    credit: Optional[CreditSignal],
    subscription: Optional[SubscriptionSignal],
    savings: Optional[SavingsSignal],
    income: Optional[IncomeSignal],
) -> Tuple[bool, Dict[str, Any]]:
    """
    Persona 5: Cash-Flow Optimizer (Priority 5 - Custom persona).
    
    Criteria (ALL of these):
    - Average monthly expenses > income by 5-15% over 30d window
    - Stable income signals present (≥2 payroll deposits)
    - Credit utilization < 50%
    
    Why this persona:
    - User overspends slightly but isn't in crisis
    - Has stable income but needs short-term budgeting
    - Not high-risk credit, just needs optimization
    - Focus: expense triage, small automation wins
    
    Note: This requires computing avg monthly expenses from transactions,
    which we'll approximate using net outflow from checking accounts.
    
    Returns:
        Tuple of (matches: bool, criteria_met: dict)
    """
    if not income:
        return False, {}
    
    criteria_met: Dict[str, Any] = {
        "persona": "cash_flow_optimizer",
        "avg_payroll_amount": float(income.avg_payroll_amount),
        "payroll_deposit_count": income.payroll_deposit_count,
        "matched_on": [],
    }
    
    # Check stable income (≥2 payroll deposits)
    stable_income = income.payroll_deposit_count >= 2
    if stable_income:
        criteria_met["matched_on"].append("stable_income_gte_2_deposits")
    
    # Check credit utilization (must be < 50%)
    credit_moderate = True
    if credit:
        credit_moderate = not credit.credit_util_flag_50
        criteria_met["credit_utilization_max_pct"] = float(credit.credit_utilization_max_pct)
        if credit_moderate:
            criteria_met["matched_on"].append("credit_util_below_50_pct")
    else:
        criteria_met["credit_utilization_max_pct"] = 0.0
        criteria_met["matched_on"].append("no_credit_cards")
    
    # Simplified expense check: low cash-flow buffer suggests slight overspending
    # If buffer is between 0.5 and 1 month, it indicates minor cash-flow issues
    slight_overspend = (
        income.cashflow_buffer_months >= Decimal("0.5") and
        income.cashflow_buffer_months <= Decimal("1.0")
    )
    criteria_met["cashflow_buffer_months"] = float(income.cashflow_buffer_months)
    if slight_overspend:
        criteria_met["matched_on"].append("cashflow_buffer_suggests_slight_overspend")
    
    # Match if: stable income AND moderate credit AND slight overspend
    matches = stable_income and credit_moderate and slight_overspend
    
    return matches, criteria_met


# Persona priority order (highest to lowest)
# This determines which persona wins when multiple match
PERSONA_CHECKS = [
    ("high_utilization", check_high_utilization),
    ("variable_income_budgeter", check_variable_income_budgeter),
    ("subscription_heavy", check_subscription_heavy),
    ("savings_builder", check_savings_builder),
    ("cash_flow_optimizer", check_cash_flow_optimizer),
]

