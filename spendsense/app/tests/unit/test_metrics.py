"""
Unit tests for evaluation metrics module.

Tests the metrics computation logic:
- Coverage metrics (users with persona + ≥3 signals)
- Explainability metrics (recommendations with rationales)
- Latency metrics (recommendation generation time)
- Auditability metrics (recommendations with decision traces)
- Metrics export (JSON and CSV formats)
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spendsense.app.db.models import (
    Base,
    CreditSignal,
    IncomeSignal,
    Persona,
    Recommendation,
    SavingsSignal,
    SubscriptionSignal,
    User,
)
from spendsense.app.eval.metrics import (
    compute_all_metrics,
    compute_auditability_metrics,
    compute_coverage_metrics,
    compute_explainability_metrics,
    export_metrics_csv,
    export_metrics_json,
)


@pytest.fixture
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_coverage_metrics_empty_database(test_db):
    """Test coverage metrics with no users."""
    metrics = compute_coverage_metrics(test_db)

    assert metrics["total_users"] == 0
    assert metrics["users_with_persona"] == 0
    assert metrics["users_with_3plus_signals"] == 0
    assert metrics["coverage_persona_pct"] == 0.0
    assert metrics["coverage_signals_pct"] == 0.0
    assert metrics["full_coverage_pct"] == 0.0


def test_coverage_metrics_with_full_coverage(test_db):
    """Test coverage metrics when all users have persona + ≥3 signals."""

    # Create 2 users
    user1 = User(user_id="user_001")
    user2 = User(user_id="user_002")
    test_db.add_all([user1, user2])
    test_db.commit()

    # Give both users personas
    persona1 = Persona(
        user_id="user_001",
        persona_id="high_utilization",
        window_days=30,
        criteria_met='{"credit_util_flag_50": true}',
    )
    persona2 = Persona(
        user_id="user_002",
        persona_id="savings_builder",
        window_days=30,
        criteria_met='{"savings_growth_pct": 3.5}',
    )
    test_db.add_all([persona1, persona2])
    test_db.commit()

    # Give both users 4 signal types (subscription, savings, credit, income)
    for user_id in ["user_001", "user_002"]:
        test_db.add(SubscriptionSignal(
            user_id=user_id,
            window_days=30,
            recurring_merchant_count=3,
            monthly_recurring_spend=Decimal("50.00"),
            subscription_share_pct=Decimal("10.0"),
        ))
        test_db.add(SavingsSignal(
            user_id=user_id,
            window_days=30,
            savings_net_inflow=Decimal("200.00"),
            savings_growth_rate_pct=Decimal("2.5"),
            emergency_fund_months=Decimal("3.0"),
        ))
        test_db.add(CreditSignal(
            user_id=user_id,
            window_days=30,
            credit_utilization_max_pct=Decimal("25.0"),
            credit_utilization_avg_pct=Decimal("20.0"),
        ))
        test_db.add(IncomeSignal(
            user_id=user_id,
            window_days=30,
            payroll_deposit_count=2,
            median_pay_gap_days=Decimal("14.0"),
            pay_gap_variability=Decimal("1.0"),
            avg_payroll_amount=Decimal("2500.00"),
            cashflow_buffer_months=Decimal("2.0"),
        ))
    test_db.commit()

    # Compute metrics
    metrics = compute_coverage_metrics(test_db)

    assert metrics["total_users"] == 2
    assert metrics["users_with_persona"] == 2
    assert metrics["users_with_3plus_signals"] == 2  # Both have 4 signals
    assert metrics["users_with_full_coverage"] == 2  # Both have persona + ≥3 signals
    assert metrics["coverage_persona_pct"] == 100.0
    assert metrics["coverage_signals_pct"] == 100.0
    assert metrics["full_coverage_pct"] == 100.0


def test_coverage_metrics_partial_coverage(test_db):
    """Test coverage metrics when some users lack persona or signals."""

    # Create 3 users
    user1 = User(user_id="user_001")
    user2 = User(user_id="user_002")
    user3 = User(user_id="user_003")
    test_db.add_all([user1, user2, user3])
    test_db.commit()

    # User 1: Has persona + 4 signals (full coverage)
    test_db.add(Persona(user_id="user_001", persona_id="high_utilization", window_days=30))

    # Create each signal type separately with only its own fields
    test_db.add(SubscriptionSignal(
        user_id="user_001",
        window_days=30,
        recurring_merchant_count=3,
        monthly_recurring_spend=Decimal("50"),
        subscription_share_pct=Decimal("10"),
    ))
    test_db.add(SavingsSignal(
        user_id="user_001",
        window_days=30,
        savings_net_inflow=Decimal("100"),
        savings_growth_rate_pct=Decimal("2"),
        emergency_fund_months=Decimal("2"),
    ))
    test_db.add(CreditSignal(
        user_id="user_001",
        window_days=30,
        credit_utilization_max_pct=Decimal("50"),
        credit_utilization_avg_pct=Decimal("45"),
    ))
    test_db.add(IncomeSignal(
        user_id="user_001",
        window_days=30,
        payroll_deposit_count=2,
        median_pay_gap_days=Decimal("14"),
        pay_gap_variability=Decimal("1"),
        avg_payroll_amount=Decimal("2500"),
        cashflow_buffer_months=Decimal("1"),
    ))

    # User 2: Has persona but only 2 signals (no full coverage)
    test_db.add(Persona(user_id="user_002", persona_id="savings_builder", window_days=30))
    test_db.add(SavingsSignal(
        user_id="user_002",
        window_days=30,
        savings_net_inflow=Decimal("100"),
        savings_growth_rate_pct=Decimal("2"),
        emergency_fund_months=Decimal("2"),
    ))
    test_db.add(IncomeSignal(
        user_id="user_002",
        window_days=30,
        payroll_deposit_count=2,
        median_pay_gap_days=Decimal("14"),
        pay_gap_variability=Decimal("1"),
        avg_payroll_amount=Decimal("2500"),
        cashflow_buffer_months=Decimal("1"),
    ))

    # User 3: No persona, no signals (no coverage)

    test_db.commit()

    # Compute metrics
    metrics = compute_coverage_metrics(test_db)

    assert metrics["total_users"] == 3
    assert metrics["users_with_persona"] == 2  # Users 1 and 2
    assert metrics["users_with_3plus_signals"] == 1  # Only user 1
    assert metrics["users_with_full_coverage"] == 1  # Only user 1
    assert metrics["coverage_persona_pct"] == round(2/3 * 100, 2)  # 66.67%
    assert metrics["coverage_signals_pct"] == round(1/3 * 100, 2)  # 33.33%
    assert metrics["full_coverage_pct"] == round(1/3 * 100, 2)  # 33.33%


def test_explainability_metrics_empty_database(test_db):
    """Test explainability metrics with no recommendations."""
    metrics = compute_explainability_metrics(test_db)

    assert metrics["total_recommendations"] == 0
    assert metrics["recommendations_with_rationale"] == 0
    assert metrics["explainability_pct"] == 0.0


def test_explainability_metrics_all_have_rationales(test_db):
    """Test explainability when all recommendations have rationales."""

    # Create 3 recommendations with rationales
    for i in range(3):
        rec = Recommendation(
            user_id=f"user_{i}",
            persona_id="high_utilization",
            window_days=30,
            item_type="education",
            title=f"Education Item {i}",
            rationale=f"Because your credit utilization is {60 + i}%",
            disclosure="This is educational content, not financial advice.",
        )
        test_db.add(rec)
    test_db.commit()

    metrics = compute_explainability_metrics(test_db)

    assert metrics["total_recommendations"] == 3
    assert metrics["recommendations_with_rationale"] == 3
    assert metrics["explainability_pct"] == 100.0


def test_explainability_metrics_partial_rationales(test_db):
    """Test explainability when some recommendations lack rationales."""

    # 2 recommendations with rationales
    test_db.add(Recommendation(
        user_id="user_1",
        persona_id="high_utilization",
        window_days=30,
        item_type="education",
        title="Item 1",
        rationale="Because utilization is 65%",
        disclosure="Disclaimer",
    ))
    test_db.add(Recommendation(
        user_id="user_2",
        persona_id="savings_builder",
        window_days=30,
        item_type="education",
        title="Item 2",
        rationale="Because savings growth is 3%",
        disclosure="Disclaimer",
    ))

    # 1 recommendation without rationale
    test_db.add(Recommendation(
        user_id="user_3",
        persona_id="subscription_heavy",
        window_days=30,
        item_type="offer",
        title="Item 3",
        rationale=None,  # Missing rationale
        disclosure="Disclaimer",
    ))
    test_db.commit()

    metrics = compute_explainability_metrics(test_db)

    assert metrics["total_recommendations"] == 3
    assert metrics["recommendations_with_rationale"] == 2
    assert metrics["explainability_pct"] == round(2/3 * 100, 2)  # 66.67%


def test_auditability_metrics_empty_database(test_db):
    """Test auditability metrics with no recommendations."""
    metrics = compute_auditability_metrics(test_db)

    assert metrics["total_recommendations"] == 0
    assert metrics["recommendations_with_traces"] == 0
    assert metrics["auditability_pct"] == 0.0


def test_auditability_metrics_all_have_traces(test_db):
    """Test auditability when all recommendations have eligibility_flags (decision traces)."""

    # Create 2 recommendations with eligibility_flags
    for i in range(2):
        rec = Recommendation(
            user_id=f"user_{i}",
            persona_id="high_utilization",
            window_days=30,
            item_type="education",
            title=f"Item {i}",
            rationale=f"Rationale {i}",
            eligibility_flags='{"tone_check": "passed", "eligibility": "qualified"}',
            disclosure="Disclaimer",
        )
        test_db.add(rec)
    test_db.commit()

    metrics = compute_auditability_metrics(test_db)

    assert metrics["total_recommendations"] == 2
    assert metrics["recommendations_with_traces"] == 2
    assert metrics["auditability_pct"] == 100.0


def test_compute_all_metrics(test_db):
    """Test compute_all_metrics returns all metric categories."""

    # Create minimal test data
    user = User(user_id="test_user")
    test_db.add(user)

    persona = Persona(user_id="test_user", persona_id="high_utilization", window_days=30)
    test_db.add(persona)

    rec = Recommendation(
        user_id="test_user",
        persona_id="high_utilization",
        window_days=30,
        item_type="education",
        title="Test Item",
        rationale="Test rationale",
        eligibility_flags='{}',
        disclosure="Disclaimer",
    )
    test_db.add(rec)
    test_db.commit()

    # Compute all metrics (skip latency for unit test speed)
    metrics = compute_all_metrics(test_db, latency_sample_size=0)

    # Verify structure
    assert "coverage" in metrics
    assert "explainability" in metrics
    assert "latency" in metrics
    assert "auditability" in metrics
    assert "metadata" in metrics

    # Verify metadata
    assert "computed_at" in metrics["metadata"]
    assert metrics["metadata"]["latency_sample_size"] == 0


def test_export_metrics_json(test_db, tmp_path):
    """Test JSON export of metrics."""

    metrics = {
        "coverage": {"total_users": 10, "full_coverage_pct": 80.0},
        "explainability": {"explainability_pct": 100.0},
        "metadata": {"computed_at": "2025-01-01 12:00:00"},
    }

    output_file = tmp_path / "test_metrics.json"
    export_metrics_json(metrics, output_file)

    # Verify file exists
    assert output_file.exists()

    # Verify content
    with open(output_file) as f:
        loaded = json.load(f)

    assert loaded["coverage"]["total_users"] == 10
    assert loaded["coverage"]["full_coverage_pct"] == 80.0
    assert loaded["explainability"]["explainability_pct"] == 100.0


def test_export_metrics_csv(test_db, tmp_path):
    """Test CSV export of metrics."""

    metrics = {
        "coverage": {
            "total_users": 10,
            "full_coverage_pct": 80.0,
        },
        "explainability": {
            "total_recommendations": 50,
            "explainability_pct": 100.0,
        },
        "metadata": {
            "computed_at": "2025-01-01 12:00:00",
        },
    }

    output_file = tmp_path / "test_metrics.csv"
    export_metrics_csv(metrics, output_file)

    # Verify file exists
    assert output_file.exists()

    # Verify content
    with open(output_file) as f:
        content = f.read()

    assert "category,metric,value" in content
    assert "coverage,total_users,10" in content
    assert "coverage,full_coverage_pct,80.0" in content
    assert "explainability,total_recommendations,50" in content
    assert "explainability,explainability_pct,100.0" in content


def test_metrics_json_and_csv_have_same_data(test_db, tmp_path):
    """Test that JSON and CSV exports contain the same metric values."""

    # Create test data
    user = User(user_id="test_user")
    persona = Persona(user_id="test_user", persona_id="test", window_days=30)
    test_db.add_all([user, persona])
    test_db.commit()

    # Compute metrics (skip latency)
    metrics = compute_all_metrics(test_db, latency_sample_size=0)

    # Export both formats
    json_file = tmp_path / "metrics.json"
    csv_file = tmp_path / "metrics.csv"
    export_metrics_json(metrics, json_file)
    export_metrics_csv(metrics, csv_file)

    # Load JSON
    with open(json_file) as f:
        json_data = json.load(f)

    # Load CSV
    csv_rows = {}
    with open(csv_file) as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) == 3:
                category, metric, value = parts
                csv_rows[f"{category}.{metric}"] = value

    # Verify key metrics match
    assert str(json_data["coverage"]["total_users"]) == csv_rows.get("coverage.total_users")
    assert str(json_data["explainability"]["total_recommendations"]) == csv_rows.get("explainability.total_recommendations")

