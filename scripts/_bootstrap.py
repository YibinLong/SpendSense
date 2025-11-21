"""
Shared helpers for CLI scripts.
"""

from pathlib import Path
import sys


def add_project_root() -> None:
    """Ensure the repository root is on sys.path for package imports."""
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

