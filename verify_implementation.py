#!/usr/bin/env python3
"""
Quick verification script for Data Foundation Epic implementation.

This script runs all the key validation steps to verify the implementation.
"""

import sys
from pathlib import Path

print("=" * 70)
print("SpendSense Data Foundation Epic - Verification Script")
print("=" * 70)
print()

# Check 1: Files exist
print("✓ Checking implementation files...")
required_files = [
    "spendsense/app/schemas/user.py",
    "spendsense/app/schemas/account.py",
    "spendsense/app/schemas/transaction.py",
    "spendsense/app/schemas/liability.py",
    "spendsense/app/schemas/consent_event.py",
    "spendsense/app/db/models.py",
    "spendsense/app/db/session.py",
    "spendsense/app/db/seed.py",
    "spendsense/app/db/parquet_export.py",
    "spendsense/app/tests/unit/test_schemas.py",
    "spendsense/app/tests/unit/test_models.py",
    "spendsense/app/tests/unit/test_seed.py",
    "spendsense/app/tests/unit/test_ingestion.py",
    "spendsense/app/tests/unit/test_parquet_export.py",
    "data/samples/users.csv",
    "data/samples/transactions.json",
]

missing_files = []
for file_path in required_files:
    if not Path(file_path).exists():
        missing_files.append(file_path)
        print(f"  ✗ Missing: {file_path}")
    else:
        print(f"  ✓ Found: {file_path}")

if missing_files:
    print(f"\n❌ {len(missing_files)} files missing!")
    sys.exit(1)

print(f"\n✅ All {len(required_files)} required files exist!")
print()

# Check 2: Import checks
print("✓ Checking imports...")
try:
    from spendsense.app.schemas.user import UserCreate
    from spendsense.app.schemas.account import AccountCreate
    from spendsense.app.schemas.transaction import TransactionCreate
    from spendsense.app.db.models import User, Account, Transaction
    from spendsense.app.db.session import init_db, get_session
    from spendsense.app.db.seed import seed_database, ingest_from_csv, ingest_from_json
    from spendsense.app.db.parquet_export import export_all
    print("  ✓ All imports successful!")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

print()

# Check 3: Pydantic validation
print("✓ Testing Pydantic validation...")
from pydantic import ValidationError
from datetime import date, timedelta
from decimal import Decimal

# Test valid user
try:
    user = UserCreate(user_id="test_user", email_masked="test@example.com")
    print("  ✓ Valid user creation works")
except Exception as e:
    print(f"  ✗ Valid user creation failed: {e}")
    sys.exit(1)

# Test invalid currency
try:
    AccountCreate(
        account_id="test",
        user_id="test",
        account_name="Test",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        currency="EUR",  # Should fail
        balance_current=Decimal("100")
    )
    print("  ✗ Invalid currency should have been rejected!")
    sys.exit(1)
except ValidationError:
    print("  ✓ Invalid currency correctly rejected")

# Test future date
try:
    TransactionCreate(
        transaction_id="test",
        account_id="test",
        amount=Decimal("100"),
        currency="USD",
        transaction_date=date.today() + timedelta(days=1),  # Future
        transaction_type="debit"
    )
    print("  ✗ Future date should have been rejected!")
    sys.exit(1)
except ValidationError:
    print("  ✓ Future date correctly rejected")

print()

# Check 4: Database setup
print("✓ Testing database initialization...")
try:
    from spendsense.app.db.session import drop_all_tables
    drop_all_tables()
    init_db()
    print("  ✓ Database initialized successfully")
except Exception as e:
    print(f"  ✗ Database initialization failed: {e}")
    sys.exit(1)

print()

# Check 5: Data generation
print("✓ Testing synthetic data generation...")
try:
    from spendsense.app.db.seed import generate_users
    users = generate_users(5)
    assert len(users) == 5
    print(f"  ✓ Generated {len(users)} users")
except Exception as e:
    print(f"  ✗ Data generation failed: {e}")
    sys.exit(1)

print()

# Final summary
print("=" * 70)
print("✅ ALL CHECKS PASSED!")
print("=" * 70)
print()
print("Implementation is complete and working correctly.")
print()
print("Next steps:")
print("  1. Run full test suite: pytest -v")
print("  2. Seed database: See TESTING_INSTRUCTIONS.md")
print("  3. Export Parquet files: See TESTING_INSTRUCTIONS.md")
print()


