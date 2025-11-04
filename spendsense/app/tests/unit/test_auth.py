"""
Unit tests for authentication module.

Tests password hashing, JWT token creation/validation, and token expiration.
"""

import pytest
from datetime import datetime, timedelta

from spendsense.app.auth.password import hash_password, verify_password
from spendsense.app.auth.jwt import create_access_token, decode_access_token


class TestPasswordHashing:
    """
    Test password hashing and verification.
    
    Why these tests:
    - Ensure passwords are never stored in plaintext
    - Verify bcrypt hashing is working correctly
    - Confirm verification succeeds for correct passwords
    - Confirm verification fails for incorrect passwords
    """
    
    def test_hash_password(self):
        """Test that password hashing produces a hash."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Hash should be a string
        assert isinstance(hashed, str)
        
        # Hash should not be the same as the password
        assert hashed != password
        
        # Hash should start with bcrypt prefix
        assert hashed.startswith("$2b$")
    
    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Verification should succeed
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        # Verification should fail
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test that empty password fails verification."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Empty password should fail
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """
    Test JWT token creation and validation.
    
    Why these tests:
    - Ensure tokens are created correctly with user data
    - Verify tokens can be decoded back to original data
    - Confirm token expiration works as expected
    """
    
    def test_create_access_token(self):
        """Test that create_access_token produces a valid JWT."""
        data = {"user_id": "test_user", "role": "card_user"}
        token = create_access_token(data)
        
        # Token should be a string
        assert isinstance(token, str)
        
        # Token should have 3 parts (header.payload.signature)
        assert len(token.split(".")) == 3
    
    def test_decode_access_token(self):
        """Test that decode_access_token correctly extracts data."""
        data = {"user_id": "test_user", "role": "card_user"}
        token = create_access_token(data)
        
        # Decode token
        decoded = decode_access_token(token)
        
        # Decoded data should match original data
        assert decoded is not None
        assert decoded["user_id"] == data["user_id"]
        assert decoded["role"] == data["role"]
        
        # Should include expiration time
        assert "exp" in decoded
    
    def test_decode_access_token_with_custom_expiration(self):
        """Test token creation with custom expiration."""
        data = {"user_id": "test_user", "role": "card_user"}
        expires_delta = timedelta(minutes=30)
        
        # Capture time before creating token to reduce time drift
        before_time = datetime.utcnow()
        token = create_access_token(data, expires_delta=expires_delta)
        after_time = datetime.utcnow()
        
        # Decode token
        decoded = decode_access_token(token)
        
        # Should have expiration time approximately 30 minutes from now
        assert decoded is not None
        
        # Use utcfromtimestamp to convert to UTC (same timezone as utcnow)
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        
        # Expected expiration should be between before_time + delta and after_time + delta
        # to account for execution time
        # Note: JWT timestamps lose microsecond precision, so we zero out microseconds
        expected_exp_min = (before_time + expires_delta).replace(microsecond=0)
        expected_exp_max = (after_time + expires_delta).replace(microsecond=0) + timedelta(seconds=1)
        
        # Token expiration should be within the expected range (allowing for timestamp truncation)
        assert exp_time >= expected_exp_min
        assert exp_time <= expected_exp_max
    
    def test_decode_invalid_token(self):
        """Test that decode_access_token raises InvalidTokenError for invalid token."""
        from spendsense.app.auth.jwt import InvalidTokenError
        
        invalid_token = "invalid.token.here"
        
        # Decoding should raise InvalidTokenError
        with pytest.raises(InvalidTokenError):
            decode_access_token(invalid_token)
    
    def test_decode_expired_token(self):
        """Test that decode_access_token raises ExpiredTokenError for expired token."""
        from spendsense.app.auth.jwt import ExpiredTokenError
        
        data = {"user_id": "test_user", "role": "card_user"}
        
        # Create token with negative expiration (already expired)
        expires_delta = timedelta(seconds=-10)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Decoding expired token should raise ExpiredTokenError
        with pytest.raises(ExpiredTokenError):
            decode_access_token(token)
    
    def test_token_includes_all_data(self):
        """Test that token preserves all provided data."""
        data = {
            "user_id": "test_user_123",
            "role": "operator",
            "email": "test@example.com",
            "custom_field": "custom_value"
        }
        token = create_access_token(data)
        
        # Decode and verify all fields present
        decoded = decode_access_token(token)
        assert decoded is not None
        
        for key, value in data.items():
            assert decoded[key] == value

