"""
Pydantic schemas for recommendations.

Why this exists:
- Validates recommendation data for API responses
- Enforces required fields like rationale and disclosure
- Provides clean request/response models for feedback
"""

import json
from datetime import datetime
from typing import Optional, Literal, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


class RecommendationItem(BaseModel):
    """
    A single recommendation (education or offer) with rationale and disclosure.
    
    Why this exists:
    - Returns personalized items with clear explanations
    - Includes mandatory educational disclaimer
    - Shows eligibility decisions for transparency
    
    Example usage:
        GET /recommendations/user_123 returns a list of these
    """
    id: int = Field(description="Database ID of the recommendation")
    user_id: str = Field(description="User identifier")
    persona_id: Optional[str] = Field(
        default=None,
        description="Persona that triggered this recommendation"
    )
    item_type: Literal["education", "offer"] = Field(
        description="Type of recommendation: education or offer"
    )
    title: str = Field(description="Recommendation title")
    description: Optional[str] = Field(
        default=None,
        description="Full description of the item"
    )
    url: Optional[str] = Field(
        default=None,
        description="Link to content or offer"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Plain-language explanation citing concrete data (e.g., 'utilization 68% on Visa 4523')"
    )
    eligibility_flags: Optional[dict[str, Any]] = Field(
        default=None,
        description="JSON object with eligibility check results"
    )
    disclosure: Optional[str] = Field(
        default=None,
        description="Mandatory educational disclaimer text"
    )
    status: str = Field(
        default="pending",
        description="Status: pending, approved, rejected"
    )
    created_at: datetime = Field(description="When this recommendation was created")
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("eligibility_flags", mode="before")
    @classmethod
    def parse_eligibility_flags(cls, v: Any) -> Optional[dict[str, Any]]:
        """Parse eligibility_flags if it's a JSON string."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class FeedbackRequest(BaseModel):
    """
    User feedback on a recommendation.
    
    Why this exists:
    - Allows users to rate or dismiss recommendations
    - Enables future improvements to the recommendation engine
    - PRD requires POST /feedback endpoint (currently a stub)
    
    Example:
        POST /feedback with {"recommendation_id": 123, "action": "helpful"}
    """
    recommendation_id: int = Field(description="ID of the recommendation being rated")
    user_id: str = Field(description="User providing feedback")
    action: Literal["helpful", "not_helpful", "dismissed"] = Field(
        description="User's feedback action"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional user notes"
    )


class FeedbackResponse(BaseModel):
    """
    Response after submitting feedback.
    """
    success: bool = Field(description="Whether feedback was recorded")
    message: str = Field(description="Confirmation message")

