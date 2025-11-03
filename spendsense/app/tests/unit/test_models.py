"""
Unit tests for SQLAlchemy ORM models.

Tests cover:
- Model creation
- Relationships
- Foreign key constraints
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from spendsense.app.db.models import User, Account, Transaction, Liability, ConsentEvent
from spendsense.app.db.session import get_session, init_db, drop_all_tables


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    drop_all_tables()
    init_db()
    yield
    drop_all_tables()


class TestUserModel:
    """Test User ORM model."""
    
    def test_create_user(self, test_db):
        """Test creating a user in the database."""
        with next(get_session()) as session:
            user = User(
                user_id="usr_test_001",
                email_masked="u***test@example.com",
                phone_masked="***-***-1111",
                created_at=datetime.utcnow()
            )
            session.add(user)
            session.commit()
            
            # Verify user was created
            fetched = session.query(User).filter(User.user_id == "usr_test_001").first()
            assert fetched is not None
            assert fetched.email_masked == "u***test@example.com"
    
    def test_unique_user_id(self, test_db):
        """Test that user_id must be unique."""
        with next(get_session()) as session:
            user1 = User(user_id="usr_duplicate", email_masked="u1@example.com", created_at=datetime.utcnow())
            user2 = User(user_id="usr_duplicate", email_masked="u2@example.com", created_at=datetime.utcnow())
            
            session.add(user1)
            session.commit()
            
            session.add(user2)
            with pytest.raises(IntegrityError):
                session.commit()


class TestAccountModel:
    """Test Account ORM model."""
    
    def test_create_account_with_user(self, test_db):
        """Test creating an account linked to a user."""
        with next(get_session()) as session:
            # Create user first
            user = User(user_id="usr_001", email_masked="u@example.com", created_at=datetime.utcnow())
            session.add(user)
            session.commit()
            
            # Create account
            account = Account(
                account_id="acc_001",
                user_id="usr_001",
                account_name="Checking",
                account_type="depository",
                account_subtype="checking",
                holder_category="individual",
                currency="USD",
                balance_current=Decimal("1000.00"),
                created_at=datetime.utcnow()
            )
            session.add(account)
            session.commit()
            
            # Verify relationship
            fetched_user = session.query(User).filter(User.user_id == "usr_001").first()
            assert len(fetched_user.accounts) == 1
            assert fetched_user.accounts[0].account_name == "Checking"


class TestTransactionModel:
    """Test Transaction ORM model."""
    
    def test_create_transaction_with_account(self, test_db):
        """Test creating a transaction linked to an account."""
        with next(get_session()) as session:
            # Create user and account
            user = User(user_id="usr_001", email_masked="u@example.com", created_at=datetime.utcnow())
            account = Account(
                account_id="acc_001",
                user_id="usr_001",
                account_name="Checking",
                account_type="depository",
                account_subtype="checking",
                holder_category="individual",
                currency="USD",
                balance_current=Decimal("1000.00"),
                created_at=datetime.utcnow()
            )
            session.add_all([user, account])
            session.commit()
            
            # Create transaction
            tx = Transaction(
                transaction_id="txn_001",
                account_id="acc_001",
                amount=Decimal("45.99"),
                currency="USD",
                transaction_date=date.today(),
                merchant_name="Starbucks",
                category="Food",
                transaction_type="debit",
                pending=False,
                created_at=datetime.utcnow()
            )
            session.add(tx)
            session.commit()
            
            # Verify relationship
            fetched_account = session.query(Account).filter(Account.account_id == "acc_001").first()
            assert len(fetched_account.transactions) == 1
            assert fetched_account.transactions[0].merchant_name == "Starbucks"


class TestLiabilityModel:
    """Test Liability ORM model."""
    
    def test_create_liability_with_user(self, test_db):
        """Test creating a liability linked to a user."""
        with next(get_session()) as session:
            # Create user
            user = User(user_id="usr_001", email_masked="u@example.com", created_at=datetime.utcnow())
            session.add(user)
            session.commit()
            
            # Create liability
            liability = Liability(
                liability_id="liab_001",
                user_id="usr_001",
                liability_type="credit_card",
                name="Chase Card",
                current_balance=Decimal("500.00"),
                credit_limit=Decimal("5000.00"),
                minimum_payment=Decimal("25.00"),
                interest_rate_percentage=Decimal("18.99"),
                is_overdue=False,
                created_at=datetime.utcnow()
            )
            session.add(liability)
            session.commit()
            
            # Verify relationship
            fetched_user = session.query(User).filter(User.user_id == "usr_001").first()
            assert len(fetched_user.liabilities) == 1
            assert fetched_user.liabilities[0].name == "Chase Card"


class TestConsentEventModel:
    """Test ConsentEvent ORM model."""
    
    def test_create_consent_event(self, test_db):
        """Test creating a consent event."""
        with next(get_session()) as session:
            # Create user
            user = User(user_id="usr_001", email_masked="u@example.com", created_at=datetime.utcnow())
            session.add(user)
            session.commit()
            
            # Create consent event
            consent = ConsentEvent(
                user_id="usr_001",
                action="opt_in",
                reason="Initial signup",
                consent_given_by="user_dashboard",
                timestamp=datetime.utcnow()
            )
            session.add(consent)
            session.commit()
            
            # Verify
            fetched = session.query(ConsentEvent).filter(ConsentEvent.user_id == "usr_001").first()
            assert fetched is not None
            assert fetched.action == "opt_in"

