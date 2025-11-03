"""
Database session management for SpendSense.

This module handles SQLite database connection and session creation.

Why this exists:
- Centralizes database connection logic
- Provides session factory for dependency injection
- Manages database initialization (create tables)
- Ensures clean session lifecycle

Usage:
    # Initialize database (creates tables)
    init_db()
    
    # Get a session for queries
    with get_session() as session:
        users = session.query(User).all()
"""

from typing import Generator

from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import Session, sessionmaker

from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Base


# Logger for this module
logger = get_logger(__name__)


# Global engine instance
# Why global? We want one engine per application lifecycle
# The engine manages the connection pool
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.
    
    Why we need this:
    - Engine is expensive to create, so we reuse a single instance
    - Manages connection pooling to SQLite database
    - Configures SQLite-specific settings
    
    Returns:
        SQLAlchemy Engine instance
    
    Example:
        engine = get_engine()
        with Session(engine) as session:
            # perform queries
    """
    global _engine
    
    if _engine is None:
        logger.info(
            "creating_database_engine",
            database_url=settings.database_url
        )
        
        # Create engine with SQLite-specific settings
        _engine = create_engine(
            settings.database_url,
            echo=settings.debug,  # Log SQL in debug mode
            # SQLite-specific settings for better concurrency
            connect_args={
                "check_same_thread": False  # Allow multi-threaded access
            }
        )
        
        # Enable foreign key support for SQLite
        # Why? SQLite doesn't enforce foreign keys by default
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Enable foreign key constraints on each connection."""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        logger.info("database_engine_created")
    
    return _engine


# Session factory
# Why sessionmaker? Creates new Session instances with consistent config
SessionLocal = sessionmaker(
    autocommit=False,  # Explicit commits for transaction safety
    autoflush=False,   # Manual flush control for better performance
    bind=None          # Will be bound to engine when needed
)


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.
    
    Why we use a generator:
    - Enables context manager pattern: `with get_session() as session:`
    - Automatically closes session when done
    - Handles exceptions gracefully
    
    This is the recommended way to get a session for FastAPI dependency injection.
    
    Yields:
        SQLAlchemy Session
    
    Example:
        with get_session() as session:
            user = session.query(User).first()
            print(user.user_id)
        # Session automatically closed here
    """
    # Ensure engine is bound
    if SessionLocal.kw.get("bind") is None:
        SessionLocal.configure(bind=get_engine())
    
    # Create session
    session = SessionLocal()
    
    try:
        logger.debug("database_session_created")
        yield session
    finally:
        # Always close session, even if exception occurs
        session.close()
        logger.debug("database_session_closed")


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    Why we need this:
    - Creates all tables defined in models.py
    - Idempotent: safe to call multiple times (won't recreate existing tables)
    - Must be called before any database operations
    
    This should be called:
    - During application startup
    - Before running tests
    - When setting up a new development environment
    
    Example:
        # Run once at app startup
        init_db()
        
        # Now database is ready for use
        with get_session() as session:
            session.add(User(user_id="u123"))
            session.commit()
    """
    logger.info("initializing_database")
    
    engine = get_engine()
    
    # Create all tables defined in Base metadata
    # This looks at all models inheriting from Base and creates their tables
    Base.metadata.create_all(bind=engine)
    
    logger.info(
        "database_initialized",
        tables=list(Base.metadata.tables.keys())
    )


def drop_all_tables() -> None:
    """
    Drop all tables from the database.
    
    ⚠️  WARNING: This deletes all data!
    
    Why this exists:
    - Useful for tests (clean slate between test runs)
    - Useful during development to reset database
    - NEVER use in production
    
    Example:
        # In test setup
        drop_all_tables()
        init_db()
        # Now you have a fresh database
    """
    logger.warning("dropping_all_tables")
    
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    
    logger.warning("all_tables_dropped")

