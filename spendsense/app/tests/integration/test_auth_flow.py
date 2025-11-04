"""
Integration tests for authentication flow.

Tests signup, login, protected routes, and role-based access control.
"""

import pytest
from fastapi.testclient import TestClient

from spendsense.app.main import app
from spendsense.app.db.session import get_session
from spendsense.app.db.models import User


@pytest.fixture
def client():
    """Test client for making HTTP requests."""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Get test database session."""
    with next(get_session()) as session:
        yield session


class TestSignupAndLogin:
    """
    Test signup and login flow.
    
    Why these tests:
    - Verify users can create accounts
    - Confirm login works with correct credentials
    - Ensure JWT tokens are returned
    - Validate token contains correct user info
    """
    
    def test_signup_success(self, client, test_db):
        """Test successful user signup."""
        # Use unique user_id to avoid conflicts with other tests
        import time
        unique_id = f"test_signup_user_{int(time.time() * 1000)}"
        
        response = client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Route returns 201 Created, not 200
        assert response.status_code == 201
        data = response.json()
        
        # Should return token
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == unique_id
        assert data["role"] == "card_user"  # Default role
    
    def test_signup_password_mismatch(self, client):
        """Test signup fails with password mismatch."""
        response = client.post(
            "/auth/signup",
            json={
                "user_id": "test_user_mismatch",
                "email_masked": "test@example.com",
                "password": "password123",
                "password_confirm": "different_password",
            }
        )
        
        # Pydantic validation returns 422 Unprocessable Entity for validation errors
        assert response.status_code == 422
        # Check that error mentions password
        response_text = str(response.json()).lower()
        assert "password" in response_text
    
    def test_signup_duplicate_user(self, client):
        """Test signup fails with duplicate user_id."""
        import time
        unique_id = f"duplicate_user_{int(time.time() * 1000)}"
        
        # First signup
        client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test1@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Second signup with same user_id
        response = client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test2@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Route returns 409 Conflict for duplicate user
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()
    
    def test_login_success(self, client):
        """Test successful login."""
        import time
        unique_id = f"login_test_user_{int(time.time() * 1000)}"
        
        # First create a user
        client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "login@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Then login
        response = client.post(
            "/auth/login",
            json={
                "username": unique_id,
                "password": "password123",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["user_id"] == unique_id
        assert data["role"] == "card_user"
    
    def test_login_wrong_password(self, client):
        """Test login fails with wrong password."""
        import time
        unique_id = f"wrong_pass_user_{int(time.time() * 1000)}"
        
        # Create user
        client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Try login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "username": unique_id,
                "password": "wrong_password",
            }
        )
        
        assert response.status_code == 401
        # Error message says "Incorrect username or password"
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent_user",
                "password": "password123",
            }
        )
        
        assert response.status_code == 401


class TestProtectedRoutes:
    """
    Test protected routes and authorization.
    
    Why these tests:
    - Ensure protected routes reject unauthenticated requests
    - Verify valid tokens grant access
    - Confirm role-based access control works
    """
    
    def test_protected_route_without_token(self, client):
        """Test protected route returns 401 without token."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_protected_route_with_invalid_token(self, client):
        """Test protected route returns 401 with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_protected_route_with_valid_token(self, client):
        """Test protected route succeeds with valid token."""
        import time
        unique_id = f"protected_route_user_{int(time.time() * 1000)}"
        
        # Create user and get token
        signup_response = client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Ensure signup was successful (201 Created)
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]
        
        # Access protected route
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == unique_id
        assert data["role"] == "card_user"
    
    def test_operator_route_requires_operator_role(self, client):
        """Test operator-only route rejects card_user."""
        import time
        unique_id = f"card_user_test_{int(time.time() * 1000)}"
        
        # Create card_user
        signup_response = client.post(
            "/auth/signup",
            json={
                "user_id": unique_id,
                "email_masked": "test@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Ensure signup was successful
        assert signup_response.status_code == 201
        token = signup_response.json()["access_token"]
        
        # Try to access operator route
        response = client.get(
            "/operator/review",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be forbidden (403)
        assert response.status_code == 403
    
    def test_user_can_only_access_own_data(self, client):
        """Test users can only access their own profile data."""
        import time
        timestamp = int(time.time() * 1000)
        user1_id = f"user1_{timestamp}"
        user2_id = f"user2_{timestamp}"
        
        # Create two users
        user1_response = client.post(
            "/auth/signup",
            json={
                "user_id": user1_id,
                "email_masked": "user1@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Ensure user1 signup was successful
        assert user1_response.status_code == 201
        user1_token = user1_response.json()["access_token"]
        
        user2_response = client.post(
            "/auth/signup",
            json={
                "user_id": user2_id,
                "email_masked": "user2@example.com",
                "password": "password123",
                "password_confirm": "password123",
            }
        )
        
        # Ensure user2 signup was successful
        assert user2_response.status_code == 201
        
        # User1 tries to access User2's profile
        response = client.get(
            f"/profile/{user2_id}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        # Should be forbidden if not operator
        # (Note: actual behavior depends on implementation)
        assert response.status_code in [403, 404]

