"""
Migration script to add window_days column to recommendations table.

This script is needed for existing databases that were created before the window_days
field was added to the Recommendation model.

Usage:
    python -m scripts.migrate_add_window_days

What it does:
- Checks if the window_days column exists in the recommendations table
- If not, adds it with a default value of 30
- Safe to run multiple times (idempotent)
"""

import sqlite3
from scripts._bootstrap import add_project_root

add_project_root()

from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger


logger = get_logger(__name__)


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate():
    """Add window_days column to recommendations table if it doesn't exist."""
    logger.info("starting_migration", script="migrate_add_window_days")
    
    # Extract database path from database URL
    # Format: sqlite:///path/to/db.db
    db_path = settings.database_url.replace("sqlite:///", "")
    
    logger.info("connecting_to_database", path=db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if window_days column already exists
        if check_column_exists(cursor, "recommendations", "window_days"):
            logger.info("migration_already_applied", column="window_days")
            print("✓ Migration already applied. The window_days column exists.")
            conn.close()
            return
        
        # Add the column
        logger.info("adding_column", table="recommendations", column="window_days")
        cursor.execute("""
            ALTER TABLE recommendations
            ADD COLUMN window_days INTEGER NOT NULL DEFAULT 30
        """)
        
        conn.commit()
        
        logger.info("migration_completed", column="window_days")
        print("✓ Successfully added window_days column to recommendations table.")
        print("  Default value: 30 days")
        
        # Show count of affected rows
        cursor.execute("SELECT COUNT(*) FROM recommendations")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  Updated {count} existing recommendation(s) with default window_days=30")
        
        conn.close()
        
    except Exception as e:
        logger.error("migration_failed", error=str(e))
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add window_days column to recommendations table")
    print("=" * 60)
    print()
    
    migrate()
    
    print()
    print("Migration complete!")

