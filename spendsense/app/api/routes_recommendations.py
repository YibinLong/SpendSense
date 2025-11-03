"""
Recommendation API routes.

This module provides endpoints for generating and managing recommendations.

Endpoints:
- GET /recommendations/{user_id} - Get personalized recommendations
- POST /feedback - Record user feedback on recommendations
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.session import get_db
from spendsense.app.db.models import User, Recommendation
from spendsense.app.schemas.recommendation import RecommendationItem, FeedbackRequest, FeedbackResponse
from spendsense.app.guardrails.consent import check_consent
from spendsense.app.recommend.engine import generate_recommendations


logger = get_logger(__name__)
router = APIRouter()


@router.get("/{user_id}", response_model=List[RecommendationItem])
async def get_recommendations(
    user_id: str,
    window: Optional[int] = Query(default=30, description="Time window in days (30 or 180)"),
    regenerate: Optional[bool] = Query(default=False, description="Force regenerate recommendations"),
    db: Session = Depends(get_db),
) -> List[RecommendationItem]:
    """
    Get personalized recommendations for a user.
    
    This endpoint requires active consent.
    Returns 3-5 education items and 1-3 partner offers with rationales.
    
    Why this exists:
    - Main recommendation endpoint
    - Returns items with concrete data-driven rationales
    - All items include mandatory educational disclaimer
    - Enforces consent and eligibility guardrails
    
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
    
    Returns 403 if consent not found.
    Returns 404 if user or persona not found.
    """
    logger.info("getting_recommendations", user_id=user_id, window_days=window)
    
    # Check consent
    if not check_consent(user_id, db):
        logger.warning("recommendations_access_denied_no_consent", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Consent required",
                "detail": f"User {user_id} has not provided consent for data processing",
                "guidance": "POST /consent with action='opt_in' to continue",
            },
        )
    
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )
    
    # Check if recommendations already exist
    if not regenerate:
        existing_recs = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
        ).all()
        
        if existing_recs:
            logger.debug("returning_existing_recommendations", user_id=user_id, count=len(existing_recs))
            return [RecommendationItem.model_validate(rec) for rec in existing_recs]
    
    # Generate new recommendations
    try:
        recommendations = generate_recommendations(user_id, window, db)
        logger.info(
            "recommendations_returned",
            user_id=user_id,
            window_days=window,
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

