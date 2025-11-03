"""
Unit tests for Parquet export functionality.

Tests cover:
- Parquet file creation
- Feature computation
- File readability
"""

import pytest
import pandas as pd
from pathlib import Path

from spendsense.app.core.config import settings
from spendsense.app.db.session import init_db, drop_all_tables, get_session
from spendsense.app.db.seed import seed_database
from spendsense.app.db.parquet_export import (
    export_transactions_denorm,
    compute_window_features,
    export_features_to_parquet,
    export_all
)


@pytest.fixture(scope="module")
def seeded_db():
    """Create database with seeded data once for all tests."""
    drop_all_tables()
    init_db()
    seed_database()
    yield
    drop_all_tables()


class TestParquetExport:
    """Test Parquet export functionality."""
    
    def test_export_transactions_denorm(self, seeded_db):
        """Test that denormalized transactions are exported correctly."""
        file_path = export_transactions_denorm()
        
        # Verify file exists
        assert Path(file_path).exists()
        
        # Verify file is readable as Parquet
        df = pd.read_parquet(file_path)
        
        # Verify expected columns
        expected_columns = [
            'transaction_id', 'transaction_date', 'amount', 'merchant_name',
            'account_id', 'account_type', 'user_id'
        ]
        for col in expected_columns:
            assert col in df.columns
        
        # Verify data exists
        assert len(df) > 0
        
        # Verify only individual accounts (not business)
        assert all(df['holder_category'] == 'individual')
    
    def test_compute_30d_features(self, seeded_db):
        """Test 30-day feature computation."""
        df = compute_window_features(30)
        
        # Verify DataFrame has data
        assert len(df) > 0
        
        # Verify expected feature columns
        expected_features = [
            'user_id', 'window_days',
            'recurring_merchant_count', 'monthly_recurring_spend',
            'savings_net_inflow', 'emergency_fund_months',
            'credit_utilization_max_pct', 'has_interest_charges',
            'payroll_deposit_count', 'cashflow_buffer_months'
        ]
        for feature in expected_features:
            assert feature in df.columns
        
        # Verify window_days is correct
        assert all(df['window_days'] == 30)
    
    def test_compute_180d_features(self, seeded_db):
        """Test 180-day feature computation."""
        df = compute_window_features(180)
        
        # Verify DataFrame has data
        assert len(df) > 0
        
        # Verify window_days is correct
        assert all(df['window_days'] == 180)
    
    def test_export_features_to_parquet(self, seeded_db):
        """Test that feature files are exported correctly."""
        paths = export_features_to_parquet()
        
        # Verify both files created
        assert '30d' in paths
        assert '180d' in paths
        
        # Verify files exist
        assert Path(paths['30d']).exists()
        assert Path(paths['180d']).exists()
        
        # Verify files are readable
        df_30d = pd.read_parquet(paths['30d'])
        df_180d = pd.read_parquet(paths['180d'])
        
        assert len(df_30d) > 0
        assert len(df_180d) > 0
    
    def test_export_all(self, seeded_db):
        """Test that export_all creates all expected files."""
        results = export_all()
        
        # Verify result structure
        assert 'transactions_denorm' in results
        assert 'features' in results
        assert '30d' in results['features']
        assert '180d' in results['features']
        
        # Verify all files exist
        assert Path(results['transactions_denorm']).exists()
        assert Path(results['features']['30d']).exists()
        assert Path(results['features']['180d']).exists()


class TestFeatureCorrectness:
    """Test that feature calculations are correct."""
    
    def test_subscription_features(self, seeded_db):
        """Test subscription-related features are reasonable."""
        df = compute_window_features(30)
        
        # Recurring merchant count should be >= 0
        assert all(df['recurring_merchant_count'] >= 0)
        
        # Monthly recurring spend should be >= 0
        assert all(df['monthly_recurring_spend'] >= 0)
        
        # Subscription share should be between 0-100%
        assert all(df['subscription_share_pct'] >= 0)
        assert all(df['subscription_share_pct'] <= 100)
    
    def test_credit_utilization_flags(self, seeded_db):
        """Test credit utilization flag logic."""
        df = compute_window_features(30)
        
        # If util >= 50, then util >= 30 should also be true
        high_util = df[df['credit_util_flag_50'] == True]
        if len(high_util) > 0:
            assert all(high_util['credit_util_flag_30'] == True)
        
        # If util >= 80, then util >= 50 should also be true
        very_high_util = df[df['credit_util_flag_80'] == True]
        if len(very_high_util) > 0:
            assert all(very_high_util['credit_util_flag_50'] == True)

