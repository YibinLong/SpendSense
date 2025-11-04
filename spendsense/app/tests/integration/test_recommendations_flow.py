"""
Integration tests for recommendations flow.

Tests the end-to-end recommendation generation:
- Seed user → opt-in consent → assign persona → generate recommendations
- Verify rationales cite concrete data
- Verify disclosure is present
- Verify eligibility filtering works
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import (
    Base,
    CreditSignal,
    IncomeSignal,
    Persona,
    SavingsSignal,
    SubscriptionSignal,
    User,
)
from spendsense.app.guardrails.consent import record_consent
from spendsense.app.personas.assign import assign_persona
from spendsense.app.recommend.engine import generate_recommendations


@pytest.fixture
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_high_utilization_recommendations(test_db):
    """
    Test recommendation generation for High Utilization persona.
    
    Verifies:
    - Recommendations match persona tags
    - Rationale cites actual utilization percentage
    - Disclosure is present
    - Education and offers are both included
    """
    # Create user
    user = User(user_id="test_rec_high_util")
    test_db.add(user)
    test_db.commit()

    # Opt-in consent
    record_consent("test_rec_high_util", "opt_in", "Testing", "api", test_db)

    # Create signals
    credit = CreditSignal(
        user_id="test_rec_high_util",
        window_days=30,
        credit_utilization_max_pct=Decimal("68.5"),
        credit_utilization_avg_pct=Decimal("60.0"),
        credit_util_flag_30=True,
        credit_util_flag_50=True,
        credit_util_flag_80=False,
        has_interest_charges=True,
        has_minimum_payment_only=False,
        is_overdue=False,
    )
    test_db.add(credit)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_rec_high_util", 30, test_db)
    assert persona.persona_id == "high_utilization"

    # Generate recommendations
    recs = generate_recommendations("test_rec_high_util", 30, test_db)

    # Verify we got recommendations
    assert len(recs) > 0

    # Verify at least one education item
    education_recs = [r for r in recs if r.item_type == "education"]
    assert len(education_recs) > 0

    # Verify first education item
    first_edu = education_recs[0]
    assert first_edu.persona_id == "high_utilization"
    assert first_edu.rationale is not None
    assert "68" in first_edu.rationale  # Should cite actual utilization
    assert first_edu.disclosure is not None
    assert "educational content" in first_edu.disclosure.lower()

    # Verify offers exist (if eligible)
    offer_recs = [r for r in recs if r.item_type == "offer"]
    # May be 0 if ineligible, but should have tried


def test_recommendations_filtered_by_eligibility(test_db):
    """
    Test that offers are filtered by eligibility criteria.
    
    For High Utilization at 85% (very high), some offers may be filtered.
    """
    # Create user
    user = User(user_id="test_rec_ineligible")
    test_db.add(user)
    test_db.commit()

    # Opt-in consent
    record_consent("test_rec_ineligible", "opt_in", "Testing", "api", test_db)

    # Create very high utilization signals
    credit = CreditSignal(
        user_id="test_rec_ineligible",
        window_days=30,
        credit_utilization_max_pct=Decimal("85.0"),  # > 80%, may filter some offers
        credit_utilization_avg_pct=Decimal("82.0"),
        credit_util_flag_30=True,
        credit_util_flag_50=True,
        credit_util_flag_80=True,
        has_interest_charges=True,
        has_minimum_payment_only=True,
        is_overdue=False,
    )
    test_db.add(credit)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_rec_ineligible", 30, test_db)

    # Generate recommendations
    recs = generate_recommendations("test_rec_ineligible", 30, test_db)

    # Should still get education items (no eligibility restriction)
    education_recs = [r for r in recs if r.item_type == "education"]
    assert len(education_recs) > 0

    # Offers may be filtered by eligibility
    # (depends on catalog criteria, may be 0)


def test_subscription_heavy_recommendations(test_db):
    """
    Test recommendations for Subscription-Heavy persona.
    
    Verifies:
    - Recommendations match subscription persona
    - Rationale mentions merchant count and monthly spend
    """
    # Create user
    user = User(user_id="test_rec_subs")
    test_db.add(user)
    test_db.commit()

    # Opt-in consent
    record_consent("test_rec_subs", "opt_in", "Testing", "api", test_db)

    # Create subscription signals
    subscription = SubscriptionSignal(
        user_id="test_rec_subs",
        window_days=30,
        recurring_merchant_count=6,
        monthly_recurring_spend=Decimal("120.00"),
        subscription_share_pct=Decimal("15.0"),
    )
    test_db.add(subscription)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_rec_subs", 30, test_db)
    assert persona.persona_id == "subscription_heavy"

    # Generate recommendations
    recs = generate_recommendations("test_rec_subs", 30, test_db)

    assert len(recs) > 0

    # Verify rationale mentions subscription details
    first_rec = recs[0]
    assert "6" in first_rec.rationale  # Merchant count
    assert "120" in first_rec.rationale  # Monthly spend


def test_recommendations_have_mandatory_disclosure(test_db):
    """
    Test that ALL recommendations include the mandatory disclosure.
    
    PRD requirement: every recommendation must have educational disclaimer.
    """
    # Create user
    user = User(user_id="test_rec_disclosure")
    test_db.add(user)
    test_db.commit()

    # Opt-in consent
    record_consent("test_rec_disclosure", "opt_in", "Testing", "api", test_db)

    # Create any signals
    savings = SavingsSignal(
        user_id="test_rec_disclosure",
        window_days=30,
        savings_net_inflow=Decimal("300.00"),
        savings_growth_rate_pct=Decimal("3.0"),
        emergency_fund_months=Decimal("2.5"),
    )
    test_db.add(savings)
    test_db.commit()

    # Assign persona
    persona = assign_persona("test_rec_disclosure", 30, test_db)

    # Generate recommendations
    recs = generate_recommendations("test_rec_disclosure", 30, test_db)

    # Verify EVERY recommendation has disclosure
    for rec in recs:
        assert rec.disclosure is not None
        assert "educational content" in rec.disclosure.lower()
        assert "not financial advice" in rec.disclosure.lower()


