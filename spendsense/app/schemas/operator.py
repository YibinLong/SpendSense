"""
Pydantic schemas for operator review workflow.

Why this exists:
- Validates operator approval/override actions
- Provides clean API responses for operator queue
- Enforces required fields like reviewer and notes
"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


class OperatorReviewResponse(BaseModel):
    """
    Operator review record.
    
    Why this exists:
    - Shows operator decisions with full traceability
    - Includes reviewer identity and decision timestamp
    - Used in operator dashboard to show review history
    
    Example usage:
        GET /operator/review returns list of these
    """
    id: int = Field(description="Database ID of the review")
    recommendation_id: int = Field(description="ID of the recommendation being reviewed")
    status: Literal["approved", "rejected", "flagged"] = Field(
        description="Operator decision"
    )
    reviewer: str = Field(description="Operator who made this decision")
    notes: Optional[str] = Field(
        default=None,
        description="Operator's notes explaining the decision"
    )
    decided_at: datetime = Field(description="When this decision was made")
    
    model_config = ConfigDict(from_attributes=True)


class ApprovalRequest(BaseModel):
    """
    Request to approve or reject a recommendation.
    
    Why this exists:
    - Validates operator actions before saving to database
    - Enforces required fields for traceability
    - Used in POST /operator/recommendations/{id}/approve
    
    Example:
        POST /operator/recommendations/123/approve
        {
            "status": "approved",
            "reviewer": "operator_alice",
            "notes": "Looks good, rationale is clear"
        }
    """
    status: Literal["approved", "rejected", "flagged"] = Field(
        description="Decision: approved, rejected, or flagged for follow-up"
    )
    reviewer: str = Field(description="Operator username or ID")
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes explaining the decision"
    )


class ApprovalResponse(BaseModel):
    """
    Response after approving/rejecting a recommendation.
    """
    success: bool = Field(description="Whether the action was successful")
    message: str = Field(description="Confirmation message")
    review_id: int = Field(description="ID of the created review record")

