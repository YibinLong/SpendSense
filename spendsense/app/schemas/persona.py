"""
Pydantic schemas for persona assignment.

Why this exists:
- Validates persona assignment data coming from the database
- Provides type-safe API response models
- Matches the Persona SQLAlchemy model structure
"""

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonaCriteria(BaseModel):
    """
    Criteria that were met for persona assignment.
    
    This provides explainability by showing exactly which conditions
    triggered the persona assignment.
    
    Example:
        {
            "credit_utilization_max_pct": 68.5,
            "credit_util_flag_50": true,
            "has_interest_charges": true
        }
    """
    # This will be a flexible dict since different personas have different criteria
    # The actual fields are populated dynamically based on the persona type


class PersonaAssignment(BaseModel):
    """
    Persona assignment response for a user in a given time window.
    
    Why we need this:
    - Returns persona ID, time window, and assignment timestamp
    - Includes criteria_met for explainability (shows WHY this persona was chosen)
    - Used in /profile endpoint responses
    
    Example usage:
        GET /profile/user_123 returns this for both 30d and 180d windows
    """
    id: int = Field(description="Database ID of the persona assignment")
    user_id: str = Field(description="User identifier")
    persona_id: str = Field(description="Assigned persona ID (e.g., 'high_utilization')")
    window_days: int = Field(description="Time window in days (30 or 180)")
    criteria_met: dict[str, Any] | None = Field(
        default=None,
        description="JSON object showing which criteria triggered this persona"
    )
    assigned_at: datetime = Field(description="When this persona was assigned")

    model_config = ConfigDict(from_attributes=True)  # Allow creation from SQLAlchemy models

    @field_validator("criteria_met", mode="before")
    @classmethod
    def parse_criteria_met(cls, v: Any) -> dict[str, Any] | None:
        """Parse criteria_met if it's a JSON string."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed: dict[str, Any] = json.loads(v)
                return parsed
            except json.JSONDecodeError:
                return None
        if isinstance(v, dict):
            return v
        return None


class PersonaCreate(BaseModel):
    """
    Request schema for creating a persona assignment.
    
    Typically used internally by the assign_persona function.
    """
    user_id: str
    persona_id: str
    window_days: int
    criteria_met: dict | None = None

