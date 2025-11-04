"""
Unit tests for CSV/JSON ingestion.

Tests cover:
- Valid data ingestion
- Validation error collection
- Partial success (some records valid, some invalid)
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from spendsense.app.db.models import Transaction, User
from spendsense.app.db.seed import ingest_from_csv, ingest_from_json
from spendsense.app.db.session import drop_all_tables, get_session, init_db


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    drop_all_tables()
    init_db()
    yield
    drop_all_tables()


class TestCSVIngestion:
    """Test CSV file ingestion."""

    def test_valid_csv_ingestion(self, test_db):
        """Test that valid CSV data is ingested successfully."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'email_masked', 'phone_masked'])
            writer.writeheader()
            writer.writerow({
                'user_id': 'usr_csv_001',
                'email_masked': 'test@example.com',
                'phone_masked': '***-***-0001'
            })
            writer.writerow({
                'user_id': 'usr_csv_002',
                'email_masked': 'test2@example.com',
                'phone_masked': '***-***-0002'
            })
            temp_path = f.name

        try:
            # Ingest
            results = ingest_from_csv(temp_path)

            # Check results
            assert results['success_count'] == 2
            assert results['error_count'] == 0

            # Verify in database
            with next(get_session()) as session:
                users = session.query(User).all()
                assert len(users) == 2
        finally:
            Path(temp_path).unlink()

    def test_invalid_csv_data(self, test_db):
        """Test that invalid CSV rows are collected as errors."""
        # Create CSV with some invalid rows
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'email_masked'])
            writer.writeheader()
            writer.writerow({'user_id': 'usr_valid', 'email_masked': 'valid@example.com'})
            writer.writerow({'user_id': '', 'email_masked': 'invalid@example.com'})  # Empty user_id
            temp_path = f.name

        try:
            results = ingest_from_csv(temp_path)

            # Should have partial success
            assert results['success_count'] == 1
            assert results['error_count'] == 1
            assert len(results['errors']) == 1
        finally:
            Path(temp_path).unlink()

    def test_missing_csv_file(self, test_db):
        """Test handling of missing CSV file."""
        results = ingest_from_csv('/nonexistent/file.csv')

        assert results['success_count'] == 0
        assert results['error_count'] == 0
        assert len(results['errors']) > 0
        assert 'not found' in results['errors'][0].lower()


class TestJSONIngestion:
    """Test JSON file ingestion."""

    def test_valid_json_ingestion(self, test_db):
        """Test that valid JSON data is ingested successfully."""
        # First create user and account for transaction reference
        with next(get_session()) as session:
            from datetime import datetime
            from decimal import Decimal

            from spendsense.app.db.models import Account, User

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

        # Create temporary JSON file with transactions
        data = [
            {
                'transaction_id': 'txn_json_001',
                'account_id': 'acc_001',
                'amount': '45.99',
                'currency': 'USD',
                'transaction_date': '2024-10-15',
                'merchant_name': 'Test Merchant',
                'transaction_type': 'debit'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            results = ingest_from_json(temp_path)

            assert results['success_count'] == 1
            assert results['error_count'] == 0
        finally:
            Path(temp_path).unlink()

    def test_invalid_json_format(self, test_db):
        """Test handling of malformed JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            results = ingest_from_json(temp_path)

            assert results['success_count'] == 0
            assert len(results['errors']) > 0
            assert 'json' in results['errors'][0].lower()
        finally:
            Path(temp_path).unlink()


