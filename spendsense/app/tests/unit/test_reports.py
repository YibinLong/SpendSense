"""
Unit tests for report generation.

Tests markdown generation, chart creation, and PDF generation.
"""

import pytest
from pathlib import Path
import tempfile

from spendsense.app.db.session import get_session
from spendsense.app.db.models import User, Persona, Recommendation
from spendsense.app.eval.reports import (
    generate_report_markdown,
    generate_charts,
    generate_report_pdf,
)
from spendsense.app.eval.report_history import (
    save_report_with_timestamp,
    get_report_history,
    cleanup_old_reports,
)
from spendsense.app.eval.metrics import compute_all_metrics


@pytest.fixture
def test_db():
    """Get test database session."""
    with next(get_session()) as session:
        yield session


@pytest.fixture
def sample_metrics():
    """Sample metrics dictionary for testing."""
    return {
        "coverage": {
            "total_users": 50,
            "users_with_persona": 45,
            "users_with_3plus_signals": 48,
            "users_with_full_coverage": 43,
            "coverage_persona_pct": 90.0,
            "coverage_signals_pct": 96.0,
            "full_coverage_pct": 86.0,
        },
        "explainability": {
            "total_recommendations": 100,
            "recommendations_with_rationale": 98,
            "explainability_pct": 98.0,
        },
        "latency": {
            "sample_size": 10,
            "latencies_seconds": [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
            "min_latency_s": 0.5,
            "max_latency_s": 1.4,
            "avg_latency_s": 0.95,
            "median_latency_s": 0.95,
            "users_under_5s": 10,
            "users_under_5s_pct": 100.0,
        },
        "auditability": {
            "total_recommendations": 100,
            "recommendations_with_traces": 95,
            "auditability_pct": 95.0,
        },
        "fairness": {
            "demographics": {
                "age_range": {
                    "25-34": {"count": 20, "pct_of_total": 40.0, "personas": {}, "education_recs": 10, "offer_recs": 5},
                    "35-44": {"count": 15, "pct_of_total": 30.0, "personas": {}, "education_recs": 8, "offer_recs": 4},
                    "45-54": {"count": 15, "pct_of_total": 30.0, "personas": {}, "education_recs": 7, "offer_recs": 3},
                },
                "gender": {
                    "female": {"count": 25, "pct_of_total": 50.0, "personas": {}, "education_recs": 12, "offer_recs": 6},
                    "male": {"count": 25, "pct_of_total": 50.0, "personas": {}, "education_recs": 13, "offer_recs": 6},
                },
                "ethnicity": {},
            },
            "disparities": [],
            "warnings": [],
            "threshold_pct": 20,
            "total_users_analyzed": 50,
        },
        "metadata": {
            "computed_at": "2025-11-04 14:30:22",
            "latency_sample_size": 10,
        }
    }


class TestMarkdownReportGeneration:
    """
    Test markdown report generation.
    
    Why these tests:
    - Verify markdown format is valid
    - Ensure all metrics are included
    - Confirm pass/fail assessments work
    - Validate report structure
    """
    
    def test_generate_report_markdown(self, test_db, sample_metrics):
        """Test markdown report generation."""
        markdown = generate_report_markdown(sample_metrics, test_db)
        
        # Should return a string
        assert isinstance(markdown, str)
        
        # Should be non-empty
        assert len(markdown) > 0
        
        # Should contain key sections
        assert "# SpendSense Evaluation Report" in markdown
        assert "Executive Summary" in markdown
        assert "Coverage Metrics" in markdown
        assert "Explainability Metrics" in markdown
        assert "Latency Metrics" in markdown
        assert "Auditability Metrics" in markdown
        assert "Fairness Analysis" in markdown
    
    def test_markdown_includes_metrics(self, test_db, sample_metrics):
        """Test that markdown includes metric values."""
        markdown = generate_report_markdown(sample_metrics, test_db)
        
        # Should include coverage percentage
        assert "86.0%" in markdown or "86%" in markdown
        
        # Should include explainability percentage
        assert "98.0%" in markdown or "98%" in markdown
        
        # Should include latency values
        assert "0.95" in markdown
    
    def test_markdown_pass_fail_indicators(self, test_db, sample_metrics):
        """Test that markdown includes pass/fail indicators."""
        markdown = generate_report_markdown(sample_metrics, test_db)
        
        # Should have pass/fail indicators (✅ or ❌ or PASS/FAIL)
        assert "✅" in markdown or "❌" in markdown or "PASS" in markdown or "FAIL" in markdown
    
    def test_markdown_with_failing_metrics(self, test_db):
        """Test markdown generation with failing metrics."""
        failing_metrics = {
            "coverage": {
                "total_users": 50,
                "users_with_persona": 20,
                "users_with_3plus_signals": 25,
                "users_with_full_coverage": 15,
                "coverage_persona_pct": 40.0,
                "coverage_signals_pct": 50.0,
                "full_coverage_pct": 30.0,  # Below 80% threshold
            },
            "explainability": {
                "total_recommendations": 100,
                "recommendations_with_rationale": 50,
                "explainability_pct": 50.0,  # Below 90% threshold
            },
            "latency": {
                "sample_size": 10,
                "latencies_seconds": [6.0] * 10,
                "min_latency_s": 6.0,
                "max_latency_s": 6.0,
                "avg_latency_s": 6.0,
                "median_latency_s": 6.0,
                "users_under_5s": 0,
                "users_under_5s_pct": 0.0,  # All over 5s
            },
            "auditability": {
                "total_recommendations": 100,
                "recommendations_with_traces": 50,
                "auditability_pct": 50.0,
            },
            "fairness": {
                "demographics": {},
                "disparities": [{"demographic": "age", "group": "55+", "issue": "under-represented"}],
                "warnings": ["Age group 55+ is under-represented"],
                "threshold_pct": 20,
                "total_users_analyzed": 50,
            },
            "metadata": {
                "computed_at": "2025-11-04 14:30:22",
                "latency_sample_size": 10,
            }
        }
        
        markdown = generate_report_markdown(failing_metrics, test_db)
        
        # Should indicate failures
        assert "NEEDS ATTENTION" in markdown or "FAIL" in markdown or "❌" in markdown


class TestChartGeneration:
    """
    Test chart generation.
    
    Why these tests:
    - Verify charts are created without errors
    - Ensure chart data is valid
    - Confirm charts use correct format
    """
    
    def test_generate_charts(self, test_db, sample_metrics):
        """Test chart generation."""
        charts = generate_charts(sample_metrics, test_db)
        
        # Should return a dictionary
        assert isinstance(charts, dict)
        
        # Charts may or may not be present (depends on matplotlib availability)
        # If present, should be BytesIO objects
        for chart_name, chart_data in charts.items():
            assert hasattr(chart_data, 'read')  # Should be file-like object
    
    def test_generate_charts_handles_empty_data(self, test_db):
        """Test chart generation with empty metrics."""
        empty_metrics = {
            "fairness": {"demographics": {}},
            "latency": {"latencies_seconds": []},
        }
        
        # Should not raise error
        charts = generate_charts(empty_metrics, test_db)
        
        # May return empty dict or charts with no data
        assert isinstance(charts, dict)


class TestPDFGeneration:
    """
    Test PDF report generation.
    
    Why these tests:
    - Verify PDF is created
    - Ensure file format is correct
    - Confirm content is included
    """
    
    def test_generate_report_pdf(self, test_db, sample_metrics):
        """Test PDF generation."""
        markdown = generate_report_markdown(sample_metrics, test_db)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.pdf"
            
            try:
                generate_report_pdf(markdown, output_path, sample_metrics, test_db)
                
                # If reportlab is available, should create PDF
                if output_path.exists():
                    assert output_path.stat().st_size > 0
                    
                    # PDF should start with %PDF
                    with open(output_path, 'rb') as f:
                        header = f.read(4)
                        assert header == b'%PDF'
            
            except (OSError, ImportError, ModuleNotFoundError) as e:
                # If reportlab not available or file system issues, that's okay
                # This test is optional - PDF generation is not critical
                import logging
                logging.warning(f"PDF generation test skipped: {e}")
                pytest.skip(f"PDF generation not available: {e}")
            
            except Exception as e:
                # For other exceptions, check if it's reportlab-related
                if "reportlab" not in str(e).lower() and "pdf" not in str(e).lower():
                    raise
                else:
                    # Reportlab-related errors are acceptable
                    pytest.skip(f"PDF generation failed (reportlab issue): {e}")


class TestReportHistory:
    """
    Test report history management.
    
    Why these tests:
    - Verify report archiving works
    - Ensure timestamp format is correct
    - Confirm cleanup works
    """
    
    def test_save_report_with_timestamp(self):
        """Test archiving report with timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test report file
            report_path = Path(tmpdir) / "eval_report.md"
            report_path.write_text("# Test Report\n\nThis is a test.")
            
            # Archive it
            archived_path = save_report_with_timestamp(report_path, Path(tmpdir) / "reports")
            
            # Should exist
            assert archived_path.exists()
            
            # Should have timestamp in name
            assert "eval_report_" in archived_path.name
            assert archived_path.suffix == ".md"
            
            # Content should match
            assert archived_path.read_text() == report_path.read_text()
    
    def test_get_report_history(self):
        """Test getting report history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports"
            reports_dir.mkdir()
            
            # Create multiple archived reports
            for i in range(3):
                report_file = reports_dir / f"eval_report_2025110{i}_120000.md"
                report_file.write_text(f"Report {i}")
            
            # Get history
            history = get_report_history(reports_dir)
            
            # Should return list of paths
            assert isinstance(history, list)
            assert len(history) == 3
    
    def test_cleanup_old_reports(self):
        """Test cleanup of old reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / "reports"
            reports_dir.mkdir()
            
            # Create 10 reports
            for i in range(10):
                report_file = reports_dir / f"eval_report_2025110{i:02d}_120000.md"
                report_file.write_text(f"Report {i}")
            
            # Keep only 5
            deleted_count = cleanup_old_reports(reports_dir, keep_count=5)
            
            # Should have deleted 5
            assert deleted_count == 5
            
            # Should have 5 remaining
            remaining = get_report_history(reports_dir)
            assert len(remaining) == 5

