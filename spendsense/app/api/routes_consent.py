"""
Consent management API routes.

This module provides endpoints for consent opt-in/opt-out.

Endpoints:
- POST /consent - Record consent action
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.session import get_db
from spendsense.app.guardrails.consent import get_consent_status, record_consent
from spendsense.app.schemas.errors import ConsentRequest, ConsentResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=ConsentResponse, status_code=status.HTTP_200_OK)
async def record_consent_action(
    consent_data: ConsentRequest,
    db: Session = Depends(get_db),
) -> ConsentResponse:
    """
    Record a consent action (opt-in or opt-out).
    
    This endpoint creates a ConsentEvent in the database and returns
    the updated consent status.
    
    Why this exists:
    - PRD requires explicit opt-in before processing
    - Users can revoke consent at any time
    - Full audit trail of consent changes
    
    Request body:
        {
            "user_id": "user_123",
            "action": "opt_in",
            "reason": "Using SpendSense dashboard",
            "by": "user_dashboard"
        }
    
    Response:
        {
            "success": true,
            "user_id": "user_123",
            "action": "opt_in",
            "message": "Consent recorded successfully"
        }
    """
    logger.info(
        "recording_consent",
        user_id=consent_data.user_id,
        action=consent_data.action,
    )

    try:
        # Record the consent event
        event = record_consent(
            user_id=consent_data.user_id,
            action=consent_data.action,
            reason=consent_data.reason,
            by=consent_data.by,
            session=db,
        )

        return ConsentResponse(
            success=True,
            user_id=consent_data.user_id,
            action=consent_data.action,
            message=f"Consent recorded successfully. User has {consent_data.action}.",
        )

    except ValueError as e:
        # Invalid user or action
        logger.error("consent_recording_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}/status")
async def get_user_consent_status(
    user_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get detailed consent status for a user.
    
    Returns consent history and current status.
    
    Response:
        {
            "has_consent": true,
            "latest_action": "opt_in",
            "latest_timestamp": "2025-11-03T10:30:00",
            "event_count": 2
        }
    """
    logger.debug("getting_consent_status", user_id=user_id)

    status = get_consent_status(user_id, db)

    return status


