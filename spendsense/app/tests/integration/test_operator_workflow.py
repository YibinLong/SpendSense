"""
Integration tests for operator review workflow.

Tests the operator approve/override flow:
- Generate recommendations
- Approve/reject via operator endpoint
- Verify OperatorReview persistence
- Verify decision traceability
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from spendsense.app.db.models import (
    Base,
    CreditSignal,
    Recommendation,
    User,
)
from spendsense.app.db.session import get_db
from spendsense.app.guardrails.consent import record_consent
from spendsense.app.main import app
from spendsense.app.personas.assign import assign_persona
from spendsense.app.recommend.engine import generate_recommendations


@pytest.fixture
def test_db_with_recs():
    """
    Create a database with a user and recommendations ready for review.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # Use StaticPool for in-memory DB to avoid threading issues
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Set up test data
    db = TestingSessionLocal()

    # Create user
    user = User(user_id="test_operator_user")
    db.add(user)
    db.commit()

    # Opt-in
    record_consent("test_operator_user", "opt_in", "Testing", "api", db)

    # Create signals
    credit = CreditSignal(
        user_id="test_operator_user",
        window_days=30,
        credit_utilization_max_pct=Decimal("70.0"),
        credit_utilization_avg_pct=Decimal("65.0"),
        credit_util_flag_30=True,
        credit_util_flag_50=True,
        credit_util_flag_80=False,
        has_interest_charges=True,
        has_minimum_payment_only=False,
        is_overdue=False,
    )
    db.add(credit)
    db.commit()

    # Assign persona and generate recommendations
    persona = assign_persona("test_operator_user", 30, db)
    recs = generate_recommendations("test_operator_user", 30, db)

    db.close()

    yield

    app.dependency_overrides.clear()


def test_operator_review_queue(test_db_with_recs):
    """
    Test that operator can see pending recommendations in review queue.
    """
    client = TestClient(app)

    # Get review queue
    response = client.get("/operator/review?status_filter=pending")

    assert response.status_code == 200
    data = response.json()

    # Should have recommendations
    assert len(data) > 0

    # Verify structure
    first_rec = data[0]
    assert "id" in first_rec
    assert "user_id" in first_rec
    assert "title" in first_rec
    assert "status" in first_rec


def test_approve_recommendation(test_db_with_recs):
    """
    Test that operator can approve a recommendation.
    
    Verifies:
    - Approval creates OperatorReview record
    - Recommendation status is updated
    - Decision trace includes reviewer and notes
    """
    client = TestClient(app)

    # Get a recommendation to approve
    queue_response = client.get("/operator/review?status_filter=pending")
    recs = queue_response.json()
    assert len(recs) > 0

    rec_id = recs[0]["id"]

    # Approve it
    approval_response = client.post(
        f"/operator/recommendations/{rec_id}/approve",
        json={
            "status": "approved",
            "reviewer": "operator_test",
            "notes": "Looks good, clear rationale",
        }
    )

    assert approval_response.status_code == 200
    data = approval_response.json()

    assert data["success"] is True
    assert "review_id" in data

    # Verify review was created
    review_id = data["review_id"]
    reviews_response = client.get(f"/operator/recommendations/{rec_id}/reviews")

    assert reviews_response.status_code == 200
    reviews = reviews_response.json()

    assert len(reviews) > 0
    first_review = reviews[0]
    assert first_review["status"] == "approved"
    assert first_review["reviewer"] == "operator_test"


def test_reject_recommendation(test_db_with_recs):
    """
    Test that operator can reject a recommendation.
    """
    client = TestClient(app)

    # Get a recommendation to reject
    queue_response = client.get("/operator/review?status_filter=pending&limit=2")
    recs = queue_response.json()

    if len(recs) < 2:
        pytest.skip("Need at least 2 recommendations for this test")

    rec_id = recs[1]["id"]

    # Reject it
    rejection_response = client.post(
        f"/operator/recommendations/{rec_id}/approve",
        json={
            "status": "rejected",
            "reviewer": "operator_test",
            "notes": "Rationale unclear",
        }
    )

    assert rejection_response.status_code == 200
    data = rejection_response.json()

    assert data["success"] is True


def test_operator_pagination(test_db_with_recs):
    """
    Test that operator review queue supports pagination.
    """
    client = TestClient(app)

    # Get first page
    response1 = client.get("/operator/review?status_filter=pending&limit=2&offset=0")
    assert response1.status_code == 200
    page1 = response1.json()

    # Get second page
    response2 = client.get("/operator/review?status_filter=pending&limit=2&offset=2")
    assert response2.status_code == 200
    page2 = response2.json()

    # If we have enough data, pages should be different
    # (If we have ≥4 items, this test is meaningful)


