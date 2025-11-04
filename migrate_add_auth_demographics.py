"""
Database migration script to add authentication and demographic fields.

This script:
1. Adds auth columns: password_hash, role, is_active to users table
2. Adds demographic columns: age_range, gender, ethnicity to users table  
3. Sets safe defaults for existing users
4. Creates default operator account

Why this exists:
- Adds new schema columns without losing existing data
- Migrates from non-auth to auth-enabled system
- Creates operator account for initial access

Run this BEFORE running seed.py on an existing database.

Usage:
    python migrate_add_auth_demographics.py
"""

import sys
from pathlib import Path

# Add parent directory to Python path so we can import spendsense modules
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text

from spendsense.app.auth.password import hash_password
from spendsense.app.core.config import settings
from spendsense.app.core.logging import configure_logging, get_logger
from spendsense.app.db.session import get_engine, get_session

# Configure logging
configure_logging(debug=settings.debug, log_level=settings.log_level)
logger = get_logger(__name__)


def run_migration() -> None:
    """
    Run the migration to add auth and demographic columns.
    
    This function:
    1. Checks if columns already exist (idempotent)
    2. Adds new columns if they don't exist
    3. Sets safe defaults for existing users
    4. Creates default operator account if it doesn't exist
    
    Why we do this:
    - Safe migration that doesn't break existing data
    - Idempotent - can be run multiple times without errors
    - Creates operator account for initial system access
    """
    logger.info("Starting database migration: add auth and demographics")
    
    with get_engine().connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(users)"))
        existing_columns = {row[1] for row in result}
        
        columns_to_add = {
            'password_hash': 'TEXT',
            'role': 'TEXT NOT NULL DEFAULT "card_user"',
            'is_active': 'BOOLEAN NOT NULL DEFAULT 1',
            'age_range': 'TEXT',
            'gender': 'TEXT',
            'ethnicity': 'TEXT',
        }
        
        # Add missing columns
        for column_name, column_def in columns_to_add.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                
                # SQLite doesn't support adding columns with NOT NULL and no default in one step
                # So we add nullable first, then update
                if 'NOT NULL' in column_def:
                    # Add as nullable first
                    base_type = column_def.split(' NOT NULL')[0]
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {base_type}"))
                    
                    # Set default value for existing rows
                    if column_name == 'role':
                        conn.execute(text(f'UPDATE users SET {column_name} = "card_user" WHERE {column_name} IS NULL'))
                    elif column_name == 'is_active':
                        conn.execute(text(f'UPDATE users SET {column_name} = 1 WHERE {column_name} IS NULL'))
                    
                    conn.commit()
                    logger.info(f"Column {column_name} added and populated with defaults")
                else:
                    # Add nullable column
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"))
                    conn.commit()
                    logger.info(f"Column {column_name} added")
            else:
                logger.debug(f"Column {column_name} already exists, skipping")
        
        logger.info("All columns added successfully")
    
    # Create default operator account if it doesn't exist
    create_default_operator()
    
    logger.info("Migration completed successfully")


def create_default_operator() -> None:
    """
    Create default operator account for system access.
    
    Creates:
    - Username: operator@spendsense.local
    - Password: operator123
    - Role: operator
    
    Why we do this:
    - Provides initial access to the system
    - Allows operators to login and create other accounts
    - Safe to run multiple times (checks if exists first)
    """
    logger.info("Creating default operator account")
    
    operator_user_id = "operator@spendsense.local"
    operator_password = "operator123"
    
    session = next(get_session())
    
    try:
        # Check if operator already exists
        result = session.execute(
            text("SELECT user_id FROM users WHERE user_id = :user_id"),
            {"user_id": operator_user_id}
        )
        
        if result.fetchone():
            logger.info("Default operator account already exists, skipping creation")
            return
        
        # Create operator account
        password_hash = hash_password(operator_password)
        
        from datetime import datetime
        
        session.execute(
            text("""
                INSERT INTO users (
                    user_id, email_masked, password_hash, role, is_active, created_at
                ) VALUES (
                    :user_id, :email, :password_hash, :role, :is_active, :created_at
                )
            """),
            {
                "user_id": operator_user_id,
                "email": "operator@spendsense.local",
                "password_hash": password_hash,
                "role": "operator",
                "is_active": 1,
                "created_at": datetime.utcnow()
            }
        )
        
        session.commit()
        
        logger.info(
            "Default operator account created",
            username=operator_user_id,
            password="operator123 (CHANGE IN PRODUCTION!)"
        )
        
        print("\n" + "="*60)
        print("DEFAULT OPERATOR ACCOUNT CREATED")
        print("="*60)
        print(f"Username: {operator_user_id}")
        print(f"Password: {operator_password}")
        print("="*60)
        print("⚠️  IMPORTANT: Change this password in production!")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Failed to create operator account: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    """
    Main entry point for migration script.
    
    Runs the migration and handles any errors.
    """
    try:
        logger.info("="*60)
        logger.info("Database Migration: Auth & Demographics")
        logger.info("="*60)
        
        run_migration()
        
        logger.info("="*60)
        logger.info("Migration completed successfully! ✓")
        logger.info("="*60)
        
        print("\n✓ Migration completed successfully!")
        print("You can now run the seed script or start the application.\n")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"\n✗ Migration failed: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

