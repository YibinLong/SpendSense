"""
Pydantic schemas for structured error responses.

Why this exists:
- Provides consistent error format across all API endpoints
- Enables better error handling in frontend
- Matches PRD requirement for structured errors with logging
"""

from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """
    Standard API error response.
    
    Why this exists:
    - Consistent error format across all endpoints
    - Includes trace ID for debugging (from structlog)
    - Provides clear error messages to frontend
    
    Used for:
    - 404 Not Found errors
    - 422 Validation errors
    - 500 Internal Server errors
    
    Example:
        {
            "error": "User not found",
            "detail": "User with ID 'user_123' does not exist",
            "trace_id": "abc123def456"
        }
    """
    error: str = Field(description="High-level error message")
    detail: str | None = Field(
        default=None,
        description="Detailed explanation of the error"
    )
    trace_id: str | None = Field(
        default=None,
        description="Request trace ID for debugging (from structlog)"
    )
    field_errors: dict[str, Any] | None = Field(
        default=None,
        description="Field-level validation errors (for 422 responses)"
    )


class ConsentError(BaseModel):
    """
    Consent-specific error response (403 Forbidden).
    
    Why this exists:
    - PRD requires blocking processing without explicit consent
    - Provides clear guidance on how to opt-in
    - Includes consent status for debugging
    
    Used when:
    - User hasn't opted in yet
    - User has revoked consent
    - Consent check fails for any reason
    
    Example:
        GET /profile/user_123 without consent returns:
        {
            "error": "Consent required",
            "detail": "Please opt-in to data processing before accessing this resource",
            "consent_status": "not_found",
            "guidance": "POST /consent with action='opt_in' to continue"
        }
    """
    error: str = Field(
        default="Consent required",
        description="Error message"
    )
    detail: str = Field(
        description="Explanation of the consent issue"
    )
    consent_status: str | None = Field(
        default=None,
        description="Current consent status: not_found, opt_out, expired"
    )
    guidance: str = Field(
        default="POST /consent with action='opt_in' to continue",
        description="How to resolve this error"
    )
    trace_id: str | None = Field(
        default=None,
        description="Request trace ID for debugging"
    )


class ConsentRequest(BaseModel):
    """
    Request schema for consent actions.
    
    Used in POST /consent endpoint.
    
    Example:
        {
            "user_id": "user_123",
            "action": "opt_in",
            "reason": "Using SpendSense dashboard",
            "by": "user_dashboard"
        }
    """
    user_id: str = Field(description="User identifier")
    action: str = Field(description="Consent action: opt_in or opt_out")
    reason: str | None = Field(
        default=None,
        description="Reason for this consent action"
    )
    by: str = Field(
        default="api",
        description="Source of consent: user_dashboard, api, operator"
    )


class ConsentResponse(BaseModel):
    """
    Response after recording consent.
    
    Returns current consent status.
    """
    success: bool = Field(description="Whether consent was recorded")
    user_id: str = Field(description="User identifier")
    action: str = Field(description="Action that was recorded")
    message: str = Field(description="Confirmation message")


