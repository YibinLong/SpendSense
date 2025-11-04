"""
Structured logging configuration using structlog.

This module sets up logging to output different formats based on environment:
- Development: Pretty-printed, human-readable logs with colors
- Production: JSON-formatted structured logs for easy parsing

Why this exists:
- Structured logs make debugging much easier than plain text
- JSON logs in production can be easily parsed by log aggregators
- Request IDs and context help trace decisions through the system
"""

import sys
import logging
from typing import Any

import structlog
from structlog.typing import EventDict, WrappedLogger


def add_app_context(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application-specific context to every log entry.
    
    This processor adds consistent metadata to all logs, making it
    easier to filter and search logs later.
    """
    event_dict["app"] = "spendsense"
    return event_dict


def configure_logging(debug: bool = True, log_level: str = "WARNING") -> None:
    """
    Configure structlog based on environment.
    
    Args:
        debug: If True, use pretty console output. If False, use JSON.
        log_level: Minimum log level to output (DEBUG, INFO, WARNING, ERROR)
    
    Why these settings:
    - In development (debug=True):
        * ConsoleRenderer creates pretty, colored output
        * Easy to read when developing locally
        * Automatically shows nice tracebacks with 'rich' if installed
    
    - In production (debug=False):
        * JSONRenderer creates machine-readable logs
        * Easy to parse and index in log aggregation systems
        * dict_tracebacks ensures exceptions are also structured
    
    - Processors (run in order):
        * merge_contextvars: Include any context variables
        * add_log_level: Add level name to each log entry
        * add_app_context: Add our custom app identifier
        * StackInfoRenderer: Show stack traces when requested
        * format_exc_info: Format exceptions nicely
        * TimeStamper: Add ISO-formatted timestamp to every log
        * ConsoleRenderer or JSONRenderer: Final output format
    """
    
    # Configure standard library logging first
    # This ensures any libraries using standard logging also work
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, log_level.upper())
    )
    
    # Shared processors used in both dev and prod
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    
    # Choose renderer based on environment
    if debug or sys.stderr.isatty():
        # Pretty printing for development
        # Check if 'rich' is available for even nicer output
        try:
            from rich.traceback import install
            install(show_locals=True)
        except ImportError:
            pass  # rich not installed, use default traceback
        
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]
    else:
        # JSON for production
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a configured logger instance.
    
    Args:
        name: Optional name for the logger (usually __name__)
    
    Returns:
        A structlog logger instance
    
    Usage:
        logger = get_logger(__name__)
        logger.info("user_action", user_id=123, action="login")
        
    Why this is useful:
    - Returns a logger that's already configured
    - Consistent logging interface across the entire app
    - Automatically includes structured data (key-value pairs)
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()


# Example usage in other modules:
#
# from spendsense.app.core.logging import get_logger
# 
# logger = get_logger(__name__)
# logger.info("processing_transaction", user_id=user_id, amount=100.50)
# logger.warning("high_utilization_detected", card_id=card_id, utilization=0.85)
# logger.error("recommendation_failed", user_id=user_id, error=str(e))

