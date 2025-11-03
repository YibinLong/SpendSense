"""
User profile API routes.

This module provides endpoints for retrieving user behavioral profiles.

Endpoints:
- GET /profile/{user_id} - Get persona and signals for 30d and 180d windows
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.session import get_db
from spendsense.app.db.models import (
    User,
    Persona,
    SubscriptionSignal,
    SavingsSignal,
    CreditSignal,
    IncomeSignal,
)
from spendsense.app.schemas.signal import (
    SignalSummary,
    SubscriptionSignalData,
    SavingsSignalData,
    CreditSignalData,
    IncomeSignalData,
)
from spendsense.app.schemas.persona import PersonaAssignment
from spendsense.app.guardrails.consent import check_consent, get_consent_status


logger = get_logger(__name__)
router = APIRouter()


@router.get("/{user_id}")
async def get_profile(
    user_id: str,
    window: Optional[int] = Query(default=30, description="Time window in days (30 or 180)"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get user profile with persona and behavioral signals.
    
    This endpoint requires active user consent.
    Returns persona assignment and all 4 signal types for the requested window.
    
    Why this exists:
    - Central endpoint for user's behavioral profile
    - Shows persona with explainability (criteria_met)
    - Provides all signals in one response
    - Enforces consent requirement
    
    Query params:
        window: Time window in days (30 or 180), default 30
    
    Response:
        {
            "user_id": "user_123",
            "window_days": 30,
            "persona": {
                "persona_id": "high_utilization",
                "criteria_met": {...},
                "assigned_at": "2025-11-03T10:00:00"
            },
            "signals": {
                "subscriptions": {...},
                "savings": {...},
                "credit": {...},
                "income": {...}
            }
        }
    
    Returns 403 if consent not found.
    Returns 404 if user not found.
    """
    logger.info("getting_profile", user_id=user_id, window_days=window)
    
    # Check consent
    if not check_consent(user_id, db):
        logger.warning("profile_access_denied_no_consent", user_id=user_id)
        
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
    
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )
    
    # Get persona
    persona = db.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window,
    ).first()
    
    persona_data = None
    if persona:
        # Parse criteria_met JSON
        criteria = None
        if persona.criteria_met:
            try:
                criteria = json.loads(persona.criteria_met)
            except json.JSONDecodeError:
                logger.warning("invalid_criteria_json", user_id=user_id)
        
        persona_data = {
            "id": persona.id,
            "persona_id": persona.persona_id,
            "window_days": persona.window_days,
            "criteria_met": criteria,
            "assigned_at": persona.assigned_at.isoformat(),
        }
    
    # Get all signals
    subscription_signal = db.query(SubscriptionSignal).filter(
        SubscriptionSignal.user_id == user_id,
        SubscriptionSignal.window_days == window,
    ).first()
    
    savings_signal = db.query(SavingsSignal).filter(
        SavingsSignal.user_id == user_id,
        SavingsSignal.window_days == window,
    ).first()
    
    credit_signal = db.query(CreditSignal).filter(
        CreditSignal.user_id == user_id,
        CreditSignal.window_days == window,
    ).first()
    
    income_signal = db.query(IncomeSignal).filter(
        IncomeSignal.user_id == user_id,
        IncomeSignal.window_days == window,
    ).first()
    
    # Build signal summary
    signals = {
        "subscriptions": SubscriptionSignalData.model_validate(subscription_signal) if subscription_signal else None,
        "savings": SavingsSignalData.model_validate(savings_signal) if savings_signal else None,
        "credit": CreditSignalData.model_validate(credit_signal) if credit_signal else None,
        "income": IncomeSignalData.model_validate(income_signal) if income_signal else None,
    }
    
    return {
        "user_id": user_id,
        "window_days": window,
        "persona": persona_data,
        "signals": signals,
    }

