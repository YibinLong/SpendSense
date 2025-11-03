"""
Persona assignment logic for SpendSense.

This module assigns personas to users based on their behavioral signals.
It uses the priority-ordered rules from rules.py to ensure deterministic assignment.

Why this exists:
- Central logic for persona assignment across all time windows
- Enforces priority ordering (High Utilization → ... → Cash-Flow Optimizer)
- Handles "Insufficient Data" cases when signals are missing
- Persists persona assignments with explainability (criteria_met)
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    Persona,
    SubscriptionSignal,
    SavingsSignal,
    CreditSignal,
    IncomeSignal,
)
from spendsense.app.personas.rules import PERSONA_CHECKS
from spendsense.app.schemas.persona import PersonaAssignment


logger = get_logger(__name__)


def assign_persona(
    user_id: str,
    window_days: int,
    session: Session,
) -> PersonaAssignment:
    """
    Assign a persona to a user based on their behavioral signals.
    
    How it works:
    1. Fetch all 4 signal types for this user and window from database
    2. Check persona rules in priority order (High Utilization first)
    3. First matching persona wins (deterministic, no ties)
    4. If no signals exist, assign "insufficient_data" persona
    5. Save persona to database with criteria_met for explainability
    6. Return PersonaAssignment schema
    
    Why priority order matters:
    - Multiple personas might match (e.g., High Utilization + Subscription-Heavy)
    - Priority ensures we focus on most critical issue first
    - PRD specifies: High Utilization → Variable Income → Subscription → Savings → Cash-Flow
    
    Args:
        user_id: User identifier
        window_days: Time window in days (30 or 180)
        session: SQLAlchemy database session
    
    Returns:
        PersonaAssignment with persona_id, criteria_met, and timestamp
    
    Example:
        persona = assign_persona("user_123", 30, session)
        # persona.persona_id = "high_utilization"
        # persona.criteria_met = {"credit_utilization_max_pct": 68.5, ...}
    """
    logger.info(
        "assigning_persona",
        user_id=user_id,
        window_days=window_days,
    )
    
    # Fetch all signals for this user and window
    subscription_signal = session.query(SubscriptionSignal).filter(
        SubscriptionSignal.user_id == user_id,
        SubscriptionSignal.window_days == window_days,
    ).first()
    
    savings_signal = session.query(SavingsSignal).filter(
        SavingsSignal.user_id == user_id,
        SavingsSignal.window_days == window_days,
    ).first()
    
    credit_signal = session.query(CreditSignal).filter(
        CreditSignal.user_id == user_id,
        CreditSignal.window_days == window_days,
    ).first()
    
    income_signal = session.query(IncomeSignal).filter(
        IncomeSignal.user_id == user_id,
        IncomeSignal.window_days == window_days,
    ).first()
    
    logger.debug(
        "signals_fetched",
        user_id=user_id,
        window_days=window_days,
        has_subscription=subscription_signal is not None,
        has_savings=savings_signal is not None,
        has_credit=credit_signal is not None,
        has_income=income_signal is not None,
    )
    
    # Check if we have any signals at all
    has_any_signals = any([
        subscription_signal,
        savings_signal,
        credit_signal,
        income_signal,
    ])
    
    if not has_any_signals:
        # No data available, assign "insufficient_data" persona
        logger.warning(
            "insufficient_data_for_persona",
            user_id=user_id,
            window_days=window_days,
        )
        assigned_persona_id = "insufficient_data"
        criteria_met = {
            "reason": "No behavioral signals available for this time window",
            "window_days": window_days,
        }
    else:
        # Check personas in priority order
        assigned_persona_id = None
        criteria_met = {}
        
        for persona_id, check_func in PERSONA_CHECKS:
            matches, criteria = check_func(
                credit=credit_signal,
                subscription=subscription_signal,
                savings=savings_signal,
                income=income_signal,
            )
            
            if matches:
                assigned_persona_id = persona_id
                criteria_met = criteria
                logger.info(
                    "persona_matched",
                    user_id=user_id,
                    window_days=window_days,
                    persona_id=persona_id,
                    matched_on=criteria.get("matched_on", []),
                )
                break  # First match wins
        
        # If no persona matched, assign "insufficient_data"
        if not assigned_persona_id:
            logger.warning(
                "no_persona_matched",
                user_id=user_id,
                window_days=window_days,
            )
            assigned_persona_id = "insufficient_data"
            criteria_met = {
                "reason": "Signals present but no persona criteria met",
                "window_days": window_days,
            }
    
    # Check if persona already exists for this user and window
    existing_persona = session.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window_days,
    ).first()
    
    if existing_persona:
        # Update existing persona
        existing_persona.persona_id = assigned_persona_id
        existing_persona.criteria_met = json.dumps(criteria_met)
        existing_persona.assigned_at = datetime.utcnow()
        session.commit()
        session.refresh(existing_persona)
        
        logger.info(
            "persona_updated",
            user_id=user_id,
            window_days=window_days,
            persona_id=assigned_persona_id,
        )
        
        return PersonaAssignment.model_validate(existing_persona)
    else:
        # Create new persona
        new_persona = Persona(
            user_id=user_id,
            persona_id=assigned_persona_id,
            window_days=window_days,
            criteria_met=json.dumps(criteria_met),
            assigned_at=datetime.utcnow(),
        )
        session.add(new_persona)
        session.commit()
        session.refresh(new_persona)
        
        logger.info(
            "persona_created",
            user_id=user_id,
            window_days=window_days,
            persona_id=assigned_persona_id,
        )
        
        return PersonaAssignment.model_validate(new_persona)


def get_persona(
    user_id: str,
    window_days: int,
    session: Session,
) -> Optional[PersonaAssignment]:
    """
    Retrieve existing persona assignment for a user.
    
    Returns None if no persona has been assigned yet.
    
    Args:
        user_id: User identifier
        window_days: Time window in days (30 or 180)
        session: SQLAlchemy database session
    
    Returns:
        PersonaAssignment if exists, None otherwise
    """
    persona = session.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window_days,
    ).first()
    
    if persona:
        return PersonaAssignment.model_validate(persona)
    return None

