"""
Unit tests for Pydantic schemas.

Tests cover:
- Valid data validation
- Invalid data rejection
- Edge cases (negative amounts, future dates, unsupported currencies)
- Field validators
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from spendsense.app.schemas.user import UserCreate
from spendsense.app.schemas.account import AccountCreate
from spendsense.app.schemas.transaction import TransactionCreate
from spendsense.app.schemas.liability import LiabilityCreate
from spendsense.app.schemas.consent_event import ConsentEventCreate


class TestUserSchema:
    """Test User schema validation."""
    
    def test_valid_user(self):
        """Test that valid user data passes validation."""
        user = UserCreate(
            user_id="usr_001",
            email_masked="u***@example.com",
            phone_masked="***-***-1234"
        )
        assert user.user_id == "usr_001"
        assert user.email_masked == "u***@example.com"
    
    def test_empty_user_id_rejected(self):
        """Test that empty user_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                user_id="",
                email_masked="u***@example.com"
            )
        errors = exc_info.value.errors()
        assert any("user_id" in str(e) for e in errors)


class TestAccountSchema:
    """Test Account schema validation."""
    
    def test_valid_checking_account(self):
        """Test that valid checking account passes validation."""
        account = AccountCreate(
            account_id="acc_001",
            user_id="usr_001",
            account_name="Primary Checking",
            account_type="depository",
            account_subtype="checking",
            holder_category="individual",
            currency="USD",
            balance_current=Decimal("1500.00")
        )
        assert account.account_type == "depository"
        assert account.currency == "USD"
    
    def test_unsupported_currency_rejected(self):
        """Test that non-USD currency is rejected per PRD."""
        with pytest.raises(ValidationError) as exc_info:
            AccountCreate(
                account_id="acc_001",
                user_id="usr_001",
                account_name="Euro Account",
                account_type="depository",
                account_subtype="checking",
                holder_category="individual",
                currency="EUR",  # Not supported
                balance_current=Decimal("1500.00")
            )
        errors = exc_info.value.errors()
        assert any("USD" in str(e) for e in errors)
    
    def test_business_account_validated(self):
        """Test that business accounts can be created (filtered later)."""
        account = AccountCreate(
            account_id="acc_business_001",
            user_id="usr_001",
            account_name="Business Checking",
            account_type="depository",
            account_subtype="checking",
            holder_category="business",  # Will be filtered in processing
            currency="USD",
            balance_current=Decimal("5000.00")
        )
        assert account.holder_category == "business"


class TestTransactionSchema:
    """Test Transaction schema validation."""
    
    def test_valid_debit_transaction(self):
        """Test that valid debit transaction passes validation."""
        tx = TransactionCreate(
            transaction_id="txn_001",
            account_id="acc_001",
            amount=Decimal("45.99"),
            currency="USD",
            transaction_date=date.today() - timedelta(days=5),
            merchant_name="Starbucks",
            category="Food and Drink",
            transaction_type="debit"
        )
        assert tx.amount == Decimal("45.99")
        assert tx.transaction_type == "debit"
    
    def test_valid_credit_transaction(self):
        """Test that negative amount (refund/credit) is allowed."""
        tx = TransactionCreate(
            transaction_id="txn_002",
            account_id="acc_001",
            amount=Decimal("-89.99"),  # Negative is OK for credits
            currency="USD",
            transaction_date=date.today() - timedelta(days=3),
            merchant_name="Amazon Refund",
            category="Shopping",
            transaction_type="credit"
        )
        assert tx.amount == Decimal("-89.99")
    
    def test_future_date_rejected(self):
        """Test that future transaction dates are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                transaction_id="txn_003",
                account_id="acc_001",
                amount=Decimal("25.00"),
                currency="USD",
                transaction_date=date.today() + timedelta(days=1),  # Future date
                transaction_type="debit"
            )
        errors = exc_info.value.errors()
        assert any("future" in str(e).lower() for e in errors)
    
    def test_unsupported_currency_rejected(self):
        """Test that non-USD currency is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                transaction_id="txn_004",
                account_id="acc_001",
                amount=Decimal("50.00"),
                currency="GBP",  # Not supported
                transaction_date=date.today(),
                transaction_type="debit"
            )
        errors = exc_info.value.errors()
        assert any("USD" in str(e) for e in errors)


class TestLiabilitySchema:
    """Test Liability schema validation."""
    
    def test_valid_credit_card_liability(self):
        """Test that valid credit card liability passes validation."""
        liability = LiabilityCreate(
            liability_id="liab_001",
            user_id="usr_001",
            account_id="acc_cc_001",
            liability_type="credit_card",
            name="Chase Sapphire",
            current_balance=Decimal("2500.00"),
            credit_limit=Decimal("10000.00"),
            minimum_payment=Decimal("50.00"),
            interest_rate_percentage=Decimal("18.99")
        )
        assert liability.liability_type == "credit_card"
        # Test utilization calculation
        assert liability.utilization_percentage == Decimal("25.0")
    
    def test_negative_balance_rejected(self):
        """Test that negative liability balance is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LiabilityCreate(
                liability_id="liab_002",
                user_id="usr_001",
                liability_type="credit_card",
                name="Card",
                current_balance=Decimal("-100.00"),  # Negative not allowed
                credit_limit=Decimal("5000.00")
            )
        errors = exc_info.value.errors()
        assert any("balance" in str(e).lower() for e in errors)
    
    def test_utilization_with_zero_limit(self):
        """Test utilization calculation when credit limit is zero or None."""
        liability = LiabilityCreate(
            liability_id="liab_003",
            user_id="usr_001",
            liability_type="student_loan",
            name="Student Loan",
            current_balance=Decimal("20000.00"),
            credit_limit=None  # Loans don't have credit limits
        )
        # Should return None for loans
        assert liability.utilization_percentage is None


class TestConsentEventSchema:
    """Test ConsentEvent schema validation."""
    
    def test_valid_opt_in(self):
        """Test that valid opt-in consent passes validation."""
        consent = ConsentEventCreate(
            user_id="usr_001",
            action="opt_in",
            reason="Initial signup",
            consent_given_by="user_dashboard"
        )
        assert consent.action == "opt_in"
        assert consent.timestamp is not None
    
    def test_valid_opt_out(self):
        """Test that valid opt-out consent passes validation."""
        consent = ConsentEventCreate(
            user_id="usr_002",
            action="opt_out",
            reason="Privacy concerns",
            consent_given_by="api"
        )
        assert consent.action == "opt_out"


class TestEdgeCases:
    """Test edge cases across schemas."""
    
    def test_missing_required_field(self):
        """Test that missing required fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate()  # Missing user_id
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_invalid_date_format(self):
        """Test that invalid date strings are rejected."""
        with pytest.raises(ValidationError):
            TransactionCreate(
                transaction_id="txn_005",
                account_id="acc_001",
                amount=Decimal("100.00"),
                currency="USD",
                transaction_date="not-a-date",  # Invalid format
                transaction_type="debit"
            )
    
    def test_decimal_precision(self):
        """Test that decimal amounts are enforced to 2 decimal places."""
        # Valid: 2 decimal places
        tx = TransactionCreate(
            transaction_id="txn_006",
            account_id="acc_001",
            amount=Decimal("12.34"),  # 2 decimal places - valid
            currency="USD",
            transaction_date=date.today(),
            transaction_type="debit"
        )
        assert isinstance(tx.amount, Decimal)
        assert tx.amount == Decimal("12.34")
        
        # Invalid: 3 decimal places should be rejected
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                transaction_id="txn_007",
                account_id="acc_001",
                amount=Decimal("12.345"),  # 3 decimal places - invalid
                currency="USD",
                transaction_date=date.today(),
                transaction_type="debit"
            )
        errors = exc_info.value.errors()
        assert any("decimal" in str(e).lower() for e in errors)

