"""
Fairness decision traces export for SpendSense.

This module exports per-demographic decision traces to support fairness auditing.

Why this exists:
- PRD requires auditability of persona assignments and recommendations
- Enables detection of disparate impact across demographic groups
- Provides detailed traces for each demographic segment
- Supports regulatory compliance and internal audits

Output:
- ./data/decision_traces/fairness/{demographic}_{value}.json
  Example: age_range_25-34.json, gender_female.json, ethnicity_asian.json
"""

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Persona, Recommendation, User

logger = get_logger(__name__)


def export_fairness_traces(session: Session, output_dir: Path) -> None:
    """
    Export per-demographic decision traces.
    
    How it works:
    1. Group users by each demographic attribute (age_range, gender, ethnicity)
    2. For each group, export:
       - User IDs in group
       - Persona assignments with criteria
       - Recommendations with rationales
    3. Save to separate JSON files for each demographic segment
    
    Args:
        session: Database session
        output_dir: Base output directory (e.g., ./data/decision_traces/fairness/)
    """
    logger.info(f"Exporting fairness traces to {output_dir}")
    
    # Create output directory
    fairness_dir = output_dir / "fairness"
    fairness_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all active users
    all_users = session.query(User).filter(User.is_active == True).all()
    
    if not all_users:
        logger.warning("No active users found for fairness trace export")
        return
    
    # Export by age_range
    age_groups: dict[str, list[dict[str, Any]]] = {}
    
    for user in all_users:
        age = user.age_range or "unknown"
        
        if age not in age_groups:
            age_groups[age] = []
        
        # Get persona and recommendations for this user
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        
        user_trace = {
            "user_id": user.user_id,
            "age_range": user.age_range,
            "gender": user.gender,
            "ethnicity": user.ethnicity,
            "persona": {
                "persona_id": persona.persona_id if persona else None,
                "window_days": persona.window_days if persona else None,
                "criteria_met": persona.criteria_met if persona else None,
                "assigned_at": str(persona.assigned_at) if persona else None,
            },
            "recommendations": [
                {
                    "id": rec.id,
                    "item_type": rec.item_type,
                    "title": rec.title,
                    "rationale": rec.rationale,
                    "eligibility_flags": rec.eligibility_flags,
                    "status": rec.status,
                    "created_at": str(rec.created_at),
                }
                for rec in recommendations
            ],
        }
        
        age_groups[age].append(user_trace)
    
    # Write age_range traces
    for age, traces in age_groups.items():
        filename = f"age_range_{age.replace(' ', '_').replace('-', '_')}.json"
        filepath = fairness_dir / filename
        
        with open(filepath, "w") as f:
            json.dump({
                "demographic": "age_range",
                "value": age,
                "user_count": len(traces),
                "traces": traces,
            }, f, indent=2, default=str)
        
        logger.info(f"Exported {len(traces)} traces for age_range={age} to {filepath}")
    
    # Export by gender
    gender_groups: dict[str, list[dict[str, Any]]] = {}
    
    for user in all_users:
        gender = user.gender or "unknown"
        
        if gender not in gender_groups:
            gender_groups[gender] = []
        
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        
        user_trace = {
            "user_id": user.user_id,
            "age_range": user.age_range,
            "gender": user.gender,
            "ethnicity": user.ethnicity,
            "persona": {
                "persona_id": persona.persona_id if persona else None,
                "window_days": persona.window_days if persona else None,
                "criteria_met": persona.criteria_met if persona else None,
                "assigned_at": str(persona.assigned_at) if persona else None,
            },
            "recommendations": [
                {
                    "id": rec.id,
                    "item_type": rec.item_type,
                    "title": rec.title,
                    "rationale": rec.rationale,
                    "eligibility_flags": rec.eligibility_flags,
                    "status": rec.status,
                    "created_at": str(rec.created_at),
                }
                for rec in recommendations
            ],
        }
        
        gender_groups[gender].append(user_trace)
    
    # Write gender traces
    for gender, traces in gender_groups.items():
        filename = f"gender_{gender.replace(' ', '_')}.json"
        filepath = fairness_dir / filename
        
        with open(filepath, "w") as f:
            json.dump({
                "demographic": "gender",
                "value": gender,
                "user_count": len(traces),
                "traces": traces,
            }, f, indent=2, default=str)
        
        logger.info(f"Exported {len(traces)} traces for gender={gender} to {filepath}")
    
    # Export by ethnicity
    ethnicity_groups: dict[str, list[dict[str, Any]]] = {}
    
    for user in all_users:
        ethnicity = user.ethnicity or "unknown"
        
        if ethnicity not in ethnicity_groups:
            ethnicity_groups[ethnicity] = []
        
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        
        user_trace = {
            "user_id": user.user_id,
            "age_range": user.age_range,
            "gender": user.gender,
            "ethnicity": user.ethnicity,
            "persona": {
                "persona_id": persona.persona_id if persona else None,
                "window_days": persona.window_days if persona else None,
                "criteria_met": persona.criteria_met if persona else None,
                "assigned_at": str(persona.assigned_at) if persona else None,
            },
            "recommendations": [
                {
                    "id": rec.id,
                    "item_type": rec.item_type,
                    "title": rec.title,
                    "rationale": rec.rationale,
                    "eligibility_flags": rec.eligibility_flags,
                    "status": rec.status,
                    "created_at": str(rec.created_at),
                }
                for rec in recommendations
            ],
        }
        
        ethnicity_groups[ethnicity].append(user_trace)
    
    # Write ethnicity traces
    for ethnicity, traces in ethnicity_groups.items():
        filename = f"ethnicity_{ethnicity.replace(' ', '_')}.json"
        filepath = fairness_dir / filename
        
        with open(filepath, "w") as f:
            json.dump({
                "demographic": "ethnicity",
                "value": ethnicity,
                "user_count": len(traces),
                "traces": traces,
            }, f, indent=2, default=str)
        
        logger.info(f"Exported {len(traces)} traces for ethnicity={ethnicity} to {filepath}")
    
    logger.info(f"Fairness traces export complete: {len(age_groups) + len(gender_groups) + len(ethnicity_groups)} files")

