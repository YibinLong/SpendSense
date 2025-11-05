"""
Recommendation API routes.

This module provides endpoints for generating and managing recommendations.

Endpoints:
- GET /recommendations/{user_id} - Get personalized recommendations
- POST /feedback - Record user feedback on recommendations
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from spendsense.app.auth.dependencies import get_optional_user
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Recommendation, User
from spendsense.app.db.session import get_db
from spendsense.app.guardrails.consent import check_consent, get_consent_status
from spendsense.app.recommend.engine import generate_recommendations
from spendsense.app.schemas.recommendation import FeedbackRequest, FeedbackResponse, RecommendationItem

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{user_id}", response_model=list[RecommendationItem])
async def get_recommendations(
    user_id: str,
    window: int | None = Query(default=30, description="Time window in days (30 or 180)"),
    regenerate: bool | None = Query(default=False, description="Force regenerate recommendations"),
    db: Session = Depends(get_db),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> list[RecommendationItem]:
    """
    Get personalized recommendations for a user.
    
    This endpoint requires active consent UNLESS the requester is an operator.
    Operators can view any user's recommendations for monitoring and operational purposes.
    Returns 3-5 education items and 1-3 partner offers with rationales.
    
    Why this exists:
    - Main recommendation endpoint
    - Returns items with concrete data-driven rationales
    - All items include mandatory educational disclaimer
    - Enforces consent and eligibility guardrails (except for operators)
    
    Query params:
        window: Time window in days (30 or 180), default 30
        regenerate: Force regenerate recommendations (default false)
    
    Response:
        [
            {
                "id": 1,
                "user_id": "user_123",
                "persona_id": "high_utilization",
                "item_type": "education",
                "title": "Credit Utilization 101",
                "rationale": "Your utilization is 68%. Consider...",
                "disclosure": "This is educational content...",
                ...
            },
            ...
        ]
    
    Returns 403 if consent not found (and requester is not an operator).
    Returns 404 if user or persona not found.
    """
    # Check if requester is an operator
    is_operator = current_user is not None and current_user.role == "operator"
    
    logger.info("getting_recommendations", user_id=user_id, window_days=window, is_operator=is_operator)

    # Check consent (skip for operators)
    if not is_operator and not check_consent(user_id, db):
        logger.warning("recommendations_access_denied_no_consent", user_id=user_id)

        # Get detailed consent status to distinguish between opt-out and never consented
        consent_status_info = get_consent_status(user_id, db)

        # Determine consent_status for the response
        if consent_status_info["latest_action"] == "opt_out":
            consent_status = "opt_out"
            detail_msg = f"User {user_id} has opted out of data processing"
        else:
            consent_status = "not_found"
            detail_msg = f"User {user_id} has not provided consent for data processing"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Consent required",
                "detail": detail_msg,
                "consent_status": consent_status,
                "guidance": "POST /consent with action='opt_in' to continue",
            },
        )
    
    if is_operator:
        logger.info("operator_access_granted", operator_id=current_user.user_id, target_user_id=user_id)

    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # Check if recommendations already exist for this user AND window
    if not regenerate:
        existing_recs = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.window_days == window,
        ).all()

        if existing_recs:
            logger.debug("returning_existing_recommendations", user_id=user_id, window_days=window, count=len(existing_recs))
            return [RecommendationItem.model_validate(rec) for rec in existing_recs]

    # Generate new recommendations
    try:
        # Ensure window is int (should always be set by Query default, but satisfy mypy)
        window_days = window if window is not None else 30
        recommendations = generate_recommendations(user_id, window_days, db)
        logger.info(
            "recommendations_returned",
            user_id=user_id,
            window_days=window_days,
            count=len(recommendations),
        )
        return recommendations

    except Exception as e:
        logger.error(
            "recommendation_generation_failed",
            user_id=user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
) -> FeedbackResponse:
    """
    Record user feedback on a recommendation.
    
    This is a stub implementation for MVP.
    In production, this would store feedback for improving recommendations.
    
    Request body:
        {
            "recommendation_id": 123,
            "user_id": "user_123",
            "action": "helpful",
            "notes": "Great suggestion!"
        }
    
    Response:
        {
            "success": true,
            "message": "Feedback recorded successfully"
        }
    """
    logger.info(
        "recording_feedback",
        recommendation_id=feedback.recommendation_id,
        user_id=feedback.user_id,
        action=feedback.action,
    )

    # Verify recommendation exists
    rec = db.query(Recommendation).filter(Recommendation.id == feedback.recommendation_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {feedback.recommendation_id} not found",
        )

    # Stub: In production, would store feedback in a feedback table
    # For now, just log it
    logger.info(
        "feedback_stub",
        recommendation_id=feedback.recommendation_id,
        action=feedback.action,
        notes=feedback.notes,
    )

    return FeedbackResponse(
        success=True,
        message="Feedback recorded successfully (stub implementation)",
    )

