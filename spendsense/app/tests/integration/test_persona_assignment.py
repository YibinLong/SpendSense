"""
Integration tests for persona assignment.

Tests the end-to-end persona assignment flow:
- Seed user with signals
- Assign persona
- Verify priority order
- Verify criteria_met explainability
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import (
    Base,
    CreditSignal,
    IncomeSignal,
    SavingsSignal,
    SubscriptionSignal,
    User,
)
from spendsense.app.personas.assign import assign_persona


@pytest.fixture
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_high_utilization_persona_priority_1(test_db):
    """
    Test that High Utilization persona wins when multiple personas match.
    
    This verifies:
    - Priority order is enforced (High Util is priority 1)
    - Criteria_met includes correct flags
    - Persona assignment is persisted
    """
    # Create user
    user = User(user_id="test_user_high_util")
    test_db.add(user)
    test_db.commit()

    # Create signals that match BOTH High Utilization AND Subscription-Heavy
    credit = CreditSignal(
        user_id="test_user_high_util",
        window_days=30,
        credit_utilization_max_pct=Decimal("65.5"),
        credit_utilization_avg_pct=Decimal("60.0"),
        credit_util_flag_30=True,
        credit_util_flag_50=True,
        credit_util_flag_80=False,
        has_interest_charges=True,
        has_minimum_payment_only=False,
        is_overdue=False,
    )

    subscription = SubscriptionSignal(
        user_id="test_user_high_util",
        window_days=30,
        recurring_merchant_count=5,
        monthly_recurring_spend=Decimal("75.00"),
        subscription_share_pct=Decimal("12.0"),
    )

    test_db.add(credit)
    test_db.add(subscription)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_user_high_util", 30, test_db)

    # Verify High Utilization wins (priority 1)
    assert persona.persona_id == "high_utilization"
    assert persona.window_days == 30

    # Verify criteria_met explains why
    import json
    criteria = json.loads(persona.criteria_met) if isinstance(persona.criteria_met, str) else persona.criteria_met
    assert "credit_util_flag_50" in criteria["matched_on"]
    assert "has_interest_charges" in criteria["matched_on"]


def test_variable_income_budgeter_persona(test_db):
    """
    Test Variable Income Budgeter persona assignment.
    
    Verifies:
    - Both conditions must be met (pay gap > 45 AND buffer < 1)
    - Criteria_met includes both flags
    """
    # Create user
    user = User(user_id="test_user_var_income")
    test_db.add(user)
    test_db.commit()

    # Create income signal matching Variable Income criteria
    income = IncomeSignal(
        user_id="test_user_var_income",
        window_days=30,
        payroll_deposit_count=3,
        median_pay_gap_days=Decimal("50.0"),  # > 45 days
        pay_gap_variability=Decimal("15.0"),
        avg_payroll_amount=Decimal("2000.00"),
        cashflow_buffer_months=Decimal("0.8"),  # < 1 month
    )

    test_db.add(income)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_user_var_income", 30, test_db)

    # Verify Variable Income Budgeter assigned
    assert persona.persona_id == "variable_income_budgeter"

    # Verify criteria
    import json
    criteria = json.loads(persona.criteria_met) if isinstance(persona.criteria_met, str) else persona.criteria_met
    assert "median_pay_gap_above_45_days" in criteria["matched_on"]
    assert "cashflow_buffer_below_1_month" in criteria["matched_on"]


def test_subscription_heavy_persona(test_db):
    """
    Test Subscription-Heavy persona assignment.
    
    Verifies:
    - ≥3 merchants AND (≥$50/mo OR ≥10% share)
    - Criteria_met shows which conditions triggered
    """
    # Create user
    user = User(user_id="test_user_subs")
    test_db.add(user)
    test_db.commit()

    # Create subscription signal
    subscription = SubscriptionSignal(
        user_id="test_user_subs",
        window_days=30,
        recurring_merchant_count=4,  # ≥ 3
        monthly_recurring_spend=Decimal("65.00"),  # ≥ $50
        subscription_share_pct=Decimal("8.0"),  # < 10% but still matches
    )

    test_db.add(subscription)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_user_subs", 30, test_db)

    # Verify Subscription-Heavy assigned
    assert persona.persona_id == "subscription_heavy"

    # Verify criteria
    import json
    criteria = json.loads(persona.criteria_met) if isinstance(persona.criteria_met, str) else persona.criteria_met
    assert "recurring_merchants_gte_3" in criteria["matched_on"]
    assert "monthly_recurring_gte_50" in criteria["matched_on"]


def test_savings_builder_persona(test_db):
    """
    Test Savings Builder persona assignment.
    
    Verifies:
    - Growth ≥2% OR inflow ≥$200
    - AND utilization < 30%
    """
    # Create user
    user = User(user_id="test_user_saver")
    test_db.add(user)
    test_db.commit()

    # Create savings and credit signals
    savings = SavingsSignal(
        user_id="test_user_saver",
        window_days=30,
        savings_net_inflow=Decimal("250.00"),  # ≥ $200
        savings_growth_rate_pct=Decimal("1.5"),  # < 2% but inflow triggers
        emergency_fund_months=Decimal("3.0"),
    )

    credit = CreditSignal(
        user_id="test_user_saver",
        window_days=30,
        credit_utilization_max_pct=Decimal("25.0"),  # < 30%
        credit_utilization_avg_pct=Decimal("20.0"),
        credit_util_flag_30=False,
        credit_util_flag_50=False,
        credit_util_flag_80=False,
        has_interest_charges=False,
        has_minimum_payment_only=False,
        is_overdue=False,
    )

    test_db.add(savings)
    test_db.add(credit)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_user_saver", 30, test_db)

    # Verify Savings Builder assigned
    assert persona.persona_id == "savings_builder"

    # Verify criteria
    import json
    criteria = json.loads(persona.criteria_met) if isinstance(persona.criteria_met, str) else persona.criteria_met
    assert "net_inflow_gte_200_per_month" in criteria["matched_on"]
    assert "all_cards_below_30_pct" in criteria["matched_on"]


def test_insufficient_data_persona(test_db):
    """
    Test that insufficient_data persona is assigned when no signals exist.
    """
    # Create user with NO signals
    user = User(user_id="test_user_no_data")
    test_db.add(user)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_user_no_data", 30, test_db)

    # Verify insufficient_data assigned
    assert persona.persona_id == "insufficient_data"

    # Verify reason
    import json
    criteria = json.loads(persona.criteria_met) if isinstance(persona.criteria_met, str) else persona.criteria_met
    assert "reason" in criteria
    assert "No behavioral signals" in criteria["reason"]


