"""
Operator review API routes.

This module provides endpoints for operator review workflow.

Endpoints:
- GET /operator/review - List recommendations pending review (operator only)
- POST /operator/recommendations/{id}/approve - Approve/reject recommendation (operator only)
- GET /operator/recommendations/{id}/reviews - Get review history (operator only)

Auth: All endpoints require operator role
"""


from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from spendsense.app.auth.dependencies import require_operator
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import OperatorReview, Recommendation, User
from spendsense.app.db.session import get_db
from spendsense.app.schemas.operator import ApprovalRequest, ApprovalResponse, OperatorReviewResponse
from spendsense.app.schemas.recommendation import RecommendationItem
from spendsense.app.eval.traces import build_decision_trace

logger = get_logger(__name__)
router = APIRouter()


@router.get("/review", response_model=list[RecommendationItem])
async def get_review_queue(
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(default="pending", description="Filter by status"),
    limit: int | None = Query(default=20, ge=1, le=100, description="Max items to return"),
    offset: int | None = Query(default=0, ge=0, description="Offset for pagination"),
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
        operator=current_user.user_id,
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
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
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
    # Use authenticated user as reviewer (overrides any value in request body)
    review = OperatorReview(
        recommendation_id=recommendation_id,
        status=approval.status,
        reviewer=current_user.user_id,
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
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
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


@router.get("/fairness")
async def get_fairness_metrics(
    current_user: Annotated[User, Depends(require_operator)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Get fairness metrics: demographic analysis of personas and recommendations.
    
    Why this exists:
    - PRD requires fairness analysis to detect potential bias
    - Operators need visibility into demographic distribution
    - Helps identify disparate impact in persona assignment
    - Supports compliance and ethical AI practices
    
    Returns:
        {
            "demographics": {
                "age_range": {
                    "25-34": {
                        "count": 15,
                        "pct_of_total": 30.0,
                        "personas": {"saver": 8, "spender": 7},
                        "education_recs": 12,
                        "offer_recs": 8
                    },
                    ...
                },
                "gender": {...},
                "ethnicity": {...}
            },
            "disparities": [
                {
                    "demographic": "age_range",
                    "group": "55+",
                    "issue": "Representation 5.0% vs expected ~20.0%",
                    "severity": "warning"
                }
            ],
            "warnings": ["Age group '55+' is under-represented"],
            "threshold_pct": 20,
            "total_users_analyzed": 50
        }
    """
    logger.info("getting_fairness_metrics", operator=current_user.user_id)
    
    from spendsense.app.eval.metrics import compute_fairness_metrics
    
    metrics = compute_fairness_metrics(db)
    
    logger.debug(
        "fairness_metrics_computed",
        total_users=metrics.get("total_users_analyzed", 0),
        disparities_count=len(metrics.get("disparities", [])),
    )
    
    return metrics


@router.get("/trace/{user_id}")
async def get_decision_trace(
    user_id: str,
    window: int | None = Query(default=30, description="Time window in days (30 or 180)"),
    current_user: Annotated[User, Depends(require_operator)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """
    Get full decision trace for a user and window (operator only).
    
    Why this exists:
    - PRD requires operator access to decision traces ("why this recommendation was made")
    - Returns persona, signals, recommendations, and timestamps
    
    Returns 404 if user not found.
    """
    logger.info("getting_decision_trace", operator=current_user.user_id, user_id=user_id, window=window)

    # Ensure window is an int
    window_days = window if window is not None else 30

    trace = build_decision_trace(user_id, window_days, db)

    if "error" in trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=trace.get("error", "Not found"),
        )

    return trace


@router.get("/reports/latest")
async def get_latest_report(
    current_user: Annotated[User, Depends(require_operator)],
):
    """
    Get latest evaluation report (markdown).
    
    Why this exists:
    - Operators need access to system performance reports
    - Provides human-readable summary of all metrics
    - Includes pass/fail assessment vs PRD targets
    
    Returns:
        {
            "content": "# SpendSense Evaluation Report\n\n...",
            "timestamp": "2025-11-04T14:30:22",
            "exists": true
        }
    
    Returns 404 if no report exists (run `python -m scripts.run_metrics --report` first)
    """
    logger.info("getting_latest_report", operator=current_user.user_id)
    
    from pathlib import Path
    from spendsense.app.core.config import settings
    
    report_path = Path(settings.data_dir) / "eval_report.md"
    
    if not report_path.exists():
        logger.warning("report_not_found", path=str(report_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found. Run 'python -m scripts.run_metrics --report' to generate one.",
        )
    
    # Get file metadata
    import os
    import datetime
    
    stat = os.stat(report_path)
    timestamp = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    # Read report content
    content = report_path.read_text()
    
    logger.debug("report_loaded", size=len(content), timestamp=timestamp)
    
    return {
        "content": content,
        "timestamp": timestamp,
        "exists": True,
    }


@router.get("/reports/latest/pdf")
async def get_latest_report_pdf(
    current_user: Annotated[User, Depends(require_operator)],
):
    """
    Download latest evaluation report as PDF.
    
    Why this exists:
    - Provides downloadable PDF for stakeholder distribution
    - Includes charts and visualizations
    - Professional format for reporting
    
    Returns: PDF file download
    
    Returns 404 if no PDF exists (run `python -m scripts.run_metrics --report` first)
    """
    logger.info("getting_latest_report_pdf", operator=current_user.user_id)
    
    from pathlib import Path
    from fastapi.responses import FileResponse
    from spendsense.app.core.config import settings
    
    pdf_path = Path(settings.data_dir) / "eval_report.pdf"
    
    if not pdf_path.exists():
        logger.warning("pdf_not_found", path=str(pdf_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF report found. Run 'python -m scripts.run_metrics --report' to generate one.",
        )
    
    logger.debug("pdf_download", path=str(pdf_path))
    
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="spendsense_eval_report.pdf",
    )


@router.get("/metrics")
async def get_metrics(
    current_user: Annotated[User, Depends(require_operator)],
):
    """
    Get evaluation metrics (JSON format).
    
    Why this exists:
    - Provides structured metrics data for dashboard visualization
    - Returns coverage, explainability, latency, auditability metrics
    - Enables chart-based reporting instead of markdown
    
    Returns:
        {
            "coverage": {...},
            "explainability": {...},
            "latency": {...},
            "auditability": {...},
            "metadata": {...}
        }
    
    Returns 404 if no metrics file exists (run `python -m scripts.run_metrics` first)
    """
    logger.info("getting_metrics", operator=current_user.user_id)
    
    from pathlib import Path
    from spendsense.app.core.config import settings
    import json
    
    metrics_path = Path(settings.data_dir) / "eval_metrics.json"
    
    if not metrics_path.exists():
        logger.warning("metrics_not_found", path=str(metrics_path))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics found. Run 'python -m scripts.run_metrics' to generate metrics.",
        )
    
    # Read metrics content
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    logger.debug("metrics_loaded", keys=list(metrics_data.keys()))
    
    return metrics_data

