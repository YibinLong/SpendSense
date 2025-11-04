"""
Operator review API routes.

This module provides endpoints for operator review workflow.

Endpoints:
- GET /operator/review - List recommendations pending review
- POST /operator/recommendations/{id}/approve - Approve/reject recommendation
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import OperatorReview, Recommendation
from spendsense.app.db.session import get_db
from spendsense.app.schemas.operator import ApprovalRequest, ApprovalResponse, OperatorReviewResponse
from spendsense.app.schemas.recommendation import RecommendationItem

logger = get_logger(__name__)
router = APIRouter()


@router.get("/review", response_model=list[RecommendationItem])
async def get_review_queue(
    status_filter: str | None = Query(default="pending", description="Filter by status"),
    limit: int | None = Query(default=20, ge=1, le=100, description="Max items to return"),
    offset: int | None = Query(default=0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    """
    Get operator review queue.
    
    Returns recommendations that need operator review, with pagination.
    
    Why this exists:
    - Operators need to review and approve recommendations before showing to users
    - Supports filtering by status (pending, approved, rejected)
    - Paginated for large datasets
    
    Query params:
        status_filter: Filter by status (default "pending")
        limit: Max items to return (1-100, default 20)
        offset: Offset for pagination (default 0)
    
    Response:
        [
            {
                "id": 1,
                "user_id": "user_123",
                "item_type": "education",
                "title": "Credit Utilization 101",
                "rationale": "Your utilization is 68%...",
                "status": "pending",
                ...
            },
            ...
        ]
    """
    logger.info(
        "getting_review_queue",
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    # Build query
    query = db.query(Recommendation)

    if status_filter:
        query = query.filter(Recommendation.status == status_filter)

    # Apply pagination
    query = query.order_by(Recommendation.created_at.desc())
    query = query.offset(offset).limit(limit)

    recommendations = query.all()

    logger.debug(
        "review_queue_returned",
        count=len(recommendations),
        status_filter=status_filter,
    )

    return [RecommendationItem.model_validate(rec) for rec in recommendations]


@router.post("/recommendations/{recommendation_id}/approve", response_model=ApprovalResponse)
async def approve_recommendation(
    recommendation_id: int,
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    """
    Approve or reject a recommendation.
    
    Creates an OperatorReview record and updates the recommendation status.
    
    Why this exists:
    - Operator oversight for recommendation quality
    - Full traceability of approval decisions
    - Supports approve, reject, or flag actions
    
    Path params:
        recommendation_id: ID of recommendation to review
    
    Request body:
        {
            "status": "approved",
            "reviewer": "operator_alice",
            "notes": "Looks good, rationale is clear"
        }
    
    Response:
        {
            "success": true,
            "message": "Recommendation approved successfully",
            "review_id": 1
        }
    
    Returns 404 if recommendation not found.
    """
    logger.info(
        "approving_recommendation",
        recommendation_id=recommendation_id,
        status=approval.status,
        reviewer=approval.reviewer,
    )

    # Get recommendation
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        logger.warning("recommendation_not_found", recommendation_id=recommendation_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )

    # Create operator review record
    review = OperatorReview(
        recommendation_id=recommendation_id,
        status=approval.status,
        reviewer=approval.reviewer,
        notes=approval.notes,
    )

    db.add(review)

    # Update recommendation status
    rec.status = approval.status

    db.commit()
    db.refresh(review)

    logger.info(
        "recommendation_reviewed",
        recommendation_id=recommendation_id,
        review_id=review.id,
        status=approval.status,
        reviewer=approval.reviewer,
    )

    return ApprovalResponse(
        success=True,
        message=f"Recommendation {approval.status} successfully",
        review_id=review.id,
    )


@router.get("/recommendations/{recommendation_id}/reviews", response_model=list[OperatorReviewResponse])
async def get_recommendation_reviews(
    recommendation_id: int,
    db: Session = Depends(get_db),
) -> list[OperatorReviewResponse]:
    """
    Get all reviews for a specific recommendation.
    
    Shows full decision trace for a recommendation.
    
    Response:
        [
            {
                "id": 1,
                "recommendation_id": 123,
                "status": "approved",
                "reviewer": "operator_alice",
                "notes": "Looks good",
                "decided_at": "2025-11-03T11:00:00"
            }
        ]
    """
    logger.debug("getting_recommendation_reviews", recommendation_id=recommendation_id)

    reviews = db.query(OperatorReview).filter(
        OperatorReview.recommendation_id == recommendation_id
    ).order_by(OperatorReview.decided_at.desc()).all()

    return [OperatorReviewResponse.model_validate(review) for review in reviews]


