"""
Report history management for SpendSense.

This module manages historical archiving of evaluation reports.

Why this exists:
- Enables tracking of system performance over time
- Preserves historical snapshots for compliance/auditing
- Allows comparison of metrics across different time periods

Output:
- ./data/reports/eval_report_{timestamp}.md
- ./data/reports/eval_report_{timestamp}.pdf
"""

import shutil
from datetime import datetime
from pathlib import Path

from spendsense.app.core.logging import get_logger

logger = get_logger(__name__)


def save_report_with_timestamp(report_path: Path, report_dir: Path | None = None) -> Path:
    """
    Archive a report with timestamp.
    
    How it works:
    1. Generate timestamp (YYYYMMDD_HHMMSS format)
    2. Copy current report to ./data/reports/eval_report_{timestamp}.{ext}
    3. Preserve original file
    4. Return path to archived copy
    
    Args:
        report_path: Path to current report file (e.g., ./data/eval_report.md)
        report_dir: Directory to save archived reports (default: ./data/reports/)
    
    Returns:
        Path to archived report
    
    Example:
        >>> save_report_with_timestamp(Path("./data/eval_report.md"))
        Path("./data/reports/eval_report_20251104_143022.md")
    """
    if not report_path.exists():
        logger.warning(f"Report file not found: {report_path}")
        raise FileNotFoundError(f"Report file not found: {report_path}")
    
    # Default report directory
    if report_dir is None:
        report_dir = report_path.parent / "reports"
    
    # Create reports directory
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create archived filename
    stem = report_path.stem  # e.g., "eval_report"
    suffix = report_path.suffix  # e.g., ".md"
    archived_name = f"{stem}_{timestamp}{suffix}"
    archived_path = report_dir / archived_name
    
    # Copy file
    shutil.copy2(report_path, archived_path)
    
    logger.info(f"Report archived: {report_path} → {archived_path}")
    return archived_path


def get_report_history(report_dir: Path, extension: str = ".md") -> list[Path]:
    """
    Get list of historical reports, sorted by timestamp (newest first).
    
    Args:
        report_dir: Directory containing archived reports
        extension: File extension to filter (default: ".md")
    
    Returns:
        List of report paths, sorted by modification time (newest first)
    """
    if not report_dir.exists():
        logger.warning(f"Report directory not found: {report_dir}")
        return []
    
    # Get all files matching pattern
    pattern = f"eval_report_*{extension}"
    reports = list(report_dir.glob(pattern))
    
    # Sort by modification time (newest first)
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    logger.debug(f"Found {len(reports)} historical reports in {report_dir}")
    return reports


def cleanup_old_reports(report_dir: Path, keep_count: int = 10, extension: str = ".md") -> int:
    """
    Clean up old reports, keeping only the most recent N.
    
    Args:
        report_dir: Directory containing archived reports
        keep_count: Number of recent reports to keep (default: 10)
        extension: File extension to filter (default: ".md")
    
    Returns:
        Number of reports deleted
    """
    if not report_dir.exists():
        logger.warning(f"Report directory not found: {report_dir}")
        return 0
    
    # Get all reports
    reports = get_report_history(report_dir, extension)
    
    # Delete old reports (beyond keep_count)
    deleted_count = 0
    for report in reports[keep_count:]:
        try:
            report.unlink()
            deleted_count += 1
            logger.debug(f"Deleted old report: {report}")
        except Exception as e:
            logger.error(f"Error deleting report {report}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old reports, kept {keep_count} most recent")
    
    return deleted_count

