"""
Consent tracking and enforcement for SpendSense.

This module implements the PRD's consent requirements:
- Explicit opt-in required before processing
- Revocation supported
- Full audit trail
- 403 blocking for requests without consent

Why this exists:
- PRD mandates user control over data processing
- Consent is checked before /profile and /recommendations endpoints
- All consent changes are logged for compliance
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import ConsentEvent, User
from spendsense.app.db.session import get_db


logger = get_logger(__name__)


def record_consent(
    user_id: str,
    action: str,
    reason: Optional[str],
    by: str,
    session: Session,
) -> ConsentEvent:
    """
    Record a consent event (opt-in or opt-out).
    
    How it works:
    - Validates action is "opt_in" or "opt_out"
    - Creates ConsentEvent record in database
    - Logs the consent change with trace ID
    - Returns the created event
    
    Why we need this:
    - Full audit trail for compliance
    - User can see their consent history
    - Operator can verify consent status
    
    Args:
        user_id: User identifier
        action: "opt_in" or "opt_out"
        reason: Optional reason for this consent action
        by: Source of consent: "user_dashboard", "api", "operator"
        session: SQLAlchemy database session
    
    Returns:
        Created ConsentEvent
    
    Example:
        event = record_consent(
            user_id="user_123",
            action="opt_in",
            reason="Using SpendSense dashboard",
            by="user_dashboard",
            session=session,
        )
    """
    # Validate action
    if action not in ["opt_in", "opt_out"]:
        raise ValueError(f"Invalid consent action: {action}. Must be 'opt_in' or 'opt_out'")
    
    # Verify user exists
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Create consent event
    trace_id = str(uuid.uuid4())
    
    consent_event = ConsentEvent(
        user_id=user_id,
        action=action,
        reason=reason,
        consent_given_by=by,
        timestamp=datetime.utcnow(),
    )
    
    session.add(consent_event)
    session.commit()
    session.refresh(consent_event)
    
    logger.info(
        "consent_recorded",
        user_id=user_id,
        action=action,
        by=by,
        trace_id=trace_id,
    )
    
    return consent_event


def check_consent(user_id: str, session: Session) -> bool:
    """
    Check if a user has active consent.
    
    How it works:
    - Finds the most recent consent event for this user
    - Returns True if latest action is "opt_in"
    - Returns False if latest action is "opt_out" or no events exist
    
    Why we need this:
    - Called by consent middleware before protected endpoints
    - Simple, fast check using indexed query
    - Deterministic (latest event wins)
    
    Args:
        user_id: User identifier
        session: SQLAlchemy database session
    
    Returns:
        True if user has opted in, False otherwise
    
    Example:
        if check_consent("user_123", session):
            # Proceed with processing
        else:
            # Block with 403
    """
    # Get most recent consent event
    latest_event = (
        session.query(ConsentEvent)
        .filter(ConsentEvent.user_id == user_id)
        .order_by(ConsentEvent.timestamp.desc())
        .first()
    )
    
    if not latest_event:
        logger.debug("no_consent_found", user_id=user_id)
        return False
    
    has_consent = latest_event.action == "opt_in"
    
    logger.debug(
        "consent_checked",
        user_id=user_id,
        has_consent=has_consent,
        latest_action=latest_event.action,
    )
    
    return has_consent


def get_consent_status(user_id: str, session: Session) -> dict:
    """
    Get detailed consent status for a user.
    
    Returns full details including latest event and history count.
    
    Args:
        user_id: User identifier
        session: SQLAlchemy database session
    
    Returns:
        Dict with consent status details
    
    Example:
        status = get_consent_status("user_123", session)
        # {
        #     "has_consent": True,
        #     "latest_action": "opt_in",
        #     "latest_timestamp": "2025-11-03T10:30:00",
        #     "event_count": 2
        # }
    """
    latest_event = (
        session.query(ConsentEvent)
        .filter(ConsentEvent.user_id == user_id)
        .order_by(ConsentEvent.timestamp.desc())
        .first()
    )
    
    event_count = (
        session.query(ConsentEvent)
        .filter(ConsentEvent.user_id == user_id)
        .count()
    )
    
    if not latest_event:
        return {
            "has_consent": False,
            "latest_action": None,
            "latest_timestamp": None,
            "event_count": 0,
        }
    
    return {
        "has_consent": latest_event.action == "opt_in",
        "latest_action": latest_event.action,
        "latest_timestamp": latest_event.timestamp.isoformat(),
        "event_count": event_count,
    }


def require_consent(user_id: str, db: Session = Depends(get_db)) -> None:
    """
    FastAPI dependency that enforces consent requirement.
    
    This is used as a route dependency on protected endpoints.
    Raises 403 if user doesn't have active consent.
    
    How to use:
        @app.get("/profile/{user_id}", dependencies=[Depends(require_consent)])
        async def get_profile(user_id: str):
            # This only runs if consent check passes
            ...
    
    Args:
        user_id: User identifier (injected from path/query)
        db: Database session (injected by FastAPI)
    
    Raises:
        HTTPException 403 if consent not found or revoked
    """
    if not check_consent(user_id, db):
        trace_id = str(uuid.uuid4())
        
        logger.warning(
            "consent_required_blocked",
            user_id=user_id,
            trace_id=trace_id,
        )
        
        # Get detailed status for better error message
        status_info = get_consent_status(user_id, db)
        
        if status_info["latest_action"] == "opt_out":
            detail = f"User {user_id} has opted out of data processing. Consent was revoked at {status_info['latest_timestamp']}."
            consent_status = "opt_out"
        else:
            detail = f"User {user_id} has not provided consent for data processing."
            consent_status = "not_found"
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Consent required",
                "detail": detail,
                "consent_status": consent_status,
                "guidance": "POST /consent with action='opt_in' to continue",
                "trace_id": trace_id,
            },
        )

