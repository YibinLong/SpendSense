"""
Pydantic schemas for behavioral signals.

Why this exists:
- Combines all 4 signal types (subscriptions, savings, credit, income) into one response
- Provides clean API responses for /profile endpoint
- Type-safe validation of signal data
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionSignalData(BaseModel):
    """
    Subscription behavior signals.
    
    Shows recurring merchant patterns and subscription spending.
    Used for Subscription-Heavy persona detection.
    """
    recurring_merchant_count: int = Field(description="Number of recurring merchants detected")
    monthly_recurring_spend: Decimal = Field(description="Average monthly recurring spend")
    subscription_share_pct: Decimal = Field(description="Subscription spend as % of total spend")

    model_config = ConfigDict(from_attributes=True)


class SavingsSignalData(BaseModel):
    """
    Savings behavior signals.
    
    Shows savings growth and emergency fund coverage.
    Used for Savings Builder persona detection.
    """
    savings_net_inflow: Decimal = Field(description="Net inflow to savings accounts")
    savings_growth_rate_pct: Decimal = Field(description="Savings growth rate percentage")
    emergency_fund_months: Decimal = Field(description="Emergency fund coverage in months")

    model_config = ConfigDict(from_attributes=True)


class CreditSignalData(BaseModel):
    """
    Credit utilization and behavior signals.
    
    Shows credit card usage patterns and risk flags.
    Used for High Utilization persona detection (highest priority).
    """
    credit_utilization_max_pct: Decimal = Field(description="Maximum utilization across all cards")
    credit_utilization_avg_pct: Decimal = Field(description="Average utilization across all cards")
    credit_util_flag_30: bool = Field(description="Any card >= 30% utilization")
    credit_util_flag_50: bool = Field(description="Any card >= 50% utilization")
    credit_util_flag_80: bool = Field(description="Any card >= 80% utilization")
    has_interest_charges: bool = Field(description="Interest charges detected in transactions")
    has_minimum_payment_only: bool = Field(description="Minimum payment only behavior detected")
    is_overdue: bool = Field(description="Any overdue payments")

    model_config = ConfigDict(from_attributes=True)


class IncomeSignalData(BaseModel):
    """
    Income stability signals.
    
    Shows payroll frequency and cash-flow buffer.
    Used for Variable Income Budgeter persona detection.
    """
    payroll_deposit_count: int = Field(description="Number of payroll deposits detected")
    median_pay_gap_days: Decimal = Field(description="Median days between paychecks")
    pay_gap_variability: Decimal = Field(description="Variability in pay frequency")
    avg_payroll_amount: Decimal = Field(description="Average payroll deposit amount")
    cashflow_buffer_months: Decimal = Field(description="Cash-flow buffer in months")

    model_config = ConfigDict(from_attributes=True)


class SignalSummary(BaseModel):
    """
    Complete signal summary for a user in a given time window.
    
    Why this exists:
    - Aggregates all 4 signal types into one clean response
    - Used in /profile endpoint to show complete behavioral picture
    - Enables frontend to display all signals at once
    
    Example usage:
        GET /profile/user_123 returns 30d and 180d SignalSummary objects
    """
    user_id: str = Field(description="User identifier")
    window_days: int = Field(description="Time window in days (30 or 180)")

    # All 4 signal types (nullable if not yet computed)
    subscriptions: SubscriptionSignalData | None = Field(
        default=None,
        description="Subscription behavior signals"
    )
    savings: SavingsSignalData | None = Field(
        default=None,
        description="Savings behavior signals"
    )
    credit: CreditSignalData | None = Field(
        default=None,
        description="Credit utilization signals"
    )
    income: IncomeSignalData | None = Field(
        default=None,
        description="Income stability signals"
    )

