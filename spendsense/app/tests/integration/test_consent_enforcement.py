"""
Integration tests for consent enforcement.

Tests the consent guardrail:
- Access denied without consent (403)
- Access granted after opt-in (200)
- Access denied after opt-out (403)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from spendsense.app.db.models import Base, User
from spendsense.app.db.session import get_db
from spendsense.app.main import app


# Override get_db dependency for testing
@pytest.fixture
def test_db():
    """Create a fresh in-memory SQLite database for each test."""
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

    # Create a test user
    db = TestingSessionLocal()
    user = User(user_id="test_consent_user")
    db.add(user)
    db.commit()
    db.close()

    yield

    app.dependency_overrides.clear()


def test_profile_blocked_without_consent(test_db):
    """
    Test that /profile returns 403 when user hasn't opted in.
    
    PRD requirement: block processing until explicit opt-in.
    """
    client = TestClient(app)

    # Try to access profile without consent
    response = client.get("/profile/test_consent_user")

    # Should return 403
    assert response.status_code == 403

    # Error should have guidance
    data = response.json()
    assert "Consent required" in data["detail"]["error"]
    assert "opt_in" in data["detail"]["guidance"]


def test_profile_allowed_after_opt_in(test_db):
    """
    Test that /profile works after user opts in.
    """
    client = TestClient(app)

    # Opt-in
    consent_response = client.post(
        "/consent",
        json={
            "user_id": "test_consent_user",
            "action": "opt_in",
            "by": "api_test",
        }
    )
    assert consent_response.status_code == 200

    # Now profile should work (may return 404 for missing persona, but not 403)
    response = client.get("/profile/test_consent_user")

    # Should NOT return 403
    assert response.status_code != 403


def test_profile_blocked_after_opt_out(test_db):
    """
    Test that /profile is blocked after user opts out.
    
    Verifies consent can be revoked.
    """
    client = TestClient(app)

    # First opt-in
    client.post(
        "/consent",
        json={
            "user_id": "test_consent_user",
            "action": "opt_in",
            "by": "api_test",
        }
    )

    # Then opt-out
    client.post(
        "/consent",
        json={
            "user_id": "test_consent_user",
            "action": "opt_out",
            "by": "api_test",
        }
    )

    # Profile should be blocked again
    response = client.get("/profile/test_consent_user")

    assert response.status_code == 403
    data = response.json()
    assert "opt_out" in data["detail"]["consent_status"]


def test_recommendations_blocked_without_consent(test_db):
    """
    Test that /recommendations also requires consent.
    """
    client = TestClient(app)

    # Try to access recommendations without consent
    response = client.get("/recommendations/test_consent_user")

    # Should return 403
    assert response.status_code == 403


