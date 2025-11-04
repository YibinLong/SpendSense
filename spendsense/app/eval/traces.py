"""
Decision trace export for SpendSense.

This module exports per-user decision traces to JSON files for auditability.

Each trace includes:
- User identification
- Assigned persona with criteria
- All behavioral signals (subscription, savings, credit, income)
- Generated recommendations with rationales
- Timestamps and metadata

Why this exists:
- PRD requires full decision traceability
- Enables operator audit of "why" a recommendation was made
- Supports compliance and transparency requirements
- Provides detailed per-user decision history
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    CreditSignal,
    IncomeSignal,
    Persona,
    Recommendation,
    SavingsSignal,
    SubscriptionSignal,
    User,
)

logger = get_logger(__name__)


def build_decision_trace(
    user_id: str,
    window_days: int,
    session: Session,
) -> dict[str, Any]:
    """
    Build a complete decision trace for a user.
    
    How it works:
    1. Fetch user's persona for the given window
    2. Fetch all behavioral signals (4 types)
    3. Fetch all recommendations for this user and window
    4. Assemble into structured trace JSON
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        session: Database session
    
    Returns:
        Dict containing complete decision trace
    """
    logger.debug(f"Building decision trace for user={user_id}, window={window_days}d")

    # Fetch user
    user = session.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning(f"User {user_id} not found")
        return {
            "user_id": user_id,
            "error": "User not found",
        }

    # Fetch persona
    persona = session.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window_days,
    ).first()

    persona_data = None
    if persona:
        # Parse criteria_met JSON
        criteria = {}
        if persona.criteria_met:
            try:
                criteria = json.loads(persona.criteria_met)
            except json.JSONDecodeError:
                criteria = {"raw": persona.criteria_met}

        persona_data = {
            "persona_id": persona.persona_id,
            "window_days": persona.window_days,
            "assigned_at": persona.assigned_at.isoformat() if persona.assigned_at else None,
            "criteria_met": criteria,
        }

    # Fetch signals
    signals = {}

    # Subscription signal
    sub_signal = session.query(SubscriptionSignal).filter(
        SubscriptionSignal.user_id == user_id,
        SubscriptionSignal.window_days == window_days,
    ).first()
    if sub_signal:
        signals["subscription"] = {
            "recurring_merchant_count": sub_signal.recurring_merchant_count,
            "monthly_recurring_spend": float(sub_signal.monthly_recurring_spend),
            "subscription_share_pct": float(sub_signal.subscription_share_pct),
            "computed_at": sub_signal.computed_at.isoformat() if sub_signal.computed_at else None,
        }

    # Savings signal
    sav_signal = session.query(SavingsSignal).filter(
        SavingsSignal.user_id == user_id,
        SavingsSignal.window_days == window_days,
    ).first()
    if sav_signal:
        signals["savings"] = {
            "savings_net_inflow": float(sav_signal.savings_net_inflow),
            "savings_growth_rate_pct": float(sav_signal.savings_growth_rate_pct),
            "emergency_fund_months": float(sav_signal.emergency_fund_months),
            "computed_at": sav_signal.computed_at.isoformat() if sav_signal.computed_at else None,
        }

    # Credit signal
    credit_signal = session.query(CreditSignal).filter(
        CreditSignal.user_id == user_id,
        CreditSignal.window_days == window_days,
    ).first()
    if credit_signal:
        signals["credit"] = {
            "credit_utilization_max_pct": float(credit_signal.credit_utilization_max_pct),
            "credit_utilization_avg_pct": float(credit_signal.credit_utilization_avg_pct),
            "credit_util_flag_30": credit_signal.credit_util_flag_30,
            "credit_util_flag_50": credit_signal.credit_util_flag_50,
            "credit_util_flag_80": credit_signal.credit_util_flag_80,
            "has_interest_charges": credit_signal.has_interest_charges,
            "has_minimum_payment_only": credit_signal.has_minimum_payment_only,
            "is_overdue": credit_signal.is_overdue,
            "computed_at": credit_signal.computed_at.isoformat() if credit_signal.computed_at else None,
        }

    # Income signal
    income_signal = session.query(IncomeSignal).filter(
        IncomeSignal.user_id == user_id,
        IncomeSignal.window_days == window_days,
    ).first()
    if income_signal:
        signals["income"] = {
            "payroll_deposit_count": income_signal.payroll_deposit_count,
            "median_pay_gap_days": float(income_signal.median_pay_gap_days),
            "pay_gap_variability": float(income_signal.pay_gap_variability),
            "avg_payroll_amount": float(income_signal.avg_payroll_amount),
            "cashflow_buffer_months": float(income_signal.cashflow_buffer_months),
            "computed_at": income_signal.computed_at.isoformat() if income_signal.computed_at else None,
        }

    # Fetch recommendations
    recommendations = session.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.window_days == window_days,
    ).all()

    recs_data = []
    for rec in recommendations:
        # Parse eligibility_flags JSON
        eligibility = {}
        if rec.eligibility_flags:
            try:
                eligibility = json.loads(rec.eligibility_flags)
            except json.JSONDecodeError:
                eligibility = {"raw": rec.eligibility_flags}

        recs_data.append({
            "id": rec.id,
            "item_type": rec.item_type,
            "title": rec.title,
            "rationale": rec.rationale,
            "persona_id": rec.persona_id,
            "status": rec.status,
            "eligibility_flags": eligibility,
            "disclosure": rec.disclosure,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
        })

    # Assemble complete trace
    trace = {
        "user_id": user_id,
        "window_days": window_days,
        "persona": persona_data,
        "signals": signals,
        "signal_count": len(signals),
        "recommendations": recs_data,
        "recommendation_count": len(recs_data),
        "trace_generated_at": datetime.utcnow().isoformat(),
    }

    return trace


def export_decision_trace(
    user_id: str,
    window_days: int,
    session: Session,
    output_dir: Path,
) -> Path:
    """
    Export a single user's decision trace to JSON file.
    
    Args:
        user_id: User identifier
        window_days: Time window (30 or 180)
        session: Database session
        output_dir: Output directory (e.g., ./data/decision_traces/)
    
    Returns:
        Path to the exported trace file
    """
    logger.debug(f"Exporting decision trace for {user_id}")

    # Build trace
    trace = build_decision_trace(user_id, window_days, session)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write trace file
    # Sanitize user_id for filename (replace special chars)
    safe_user_id = user_id.replace("/", "_").replace("\\", "_")
    filename = f"user_{safe_user_id}_w{window_days}d.json"
    output_path = output_dir / filename

    with open(output_path, "w") as f:
        json.dump(trace, f, indent=2)

    logger.debug(f"Decision trace exported to {output_path}")
    return output_path


def export_all_decision_traces(
    session: Session,
    output_dir: Path,
    window_days: int = 30,
) -> list[Path]:
    """
    Export decision traces for all users.
    
    Args:
        session: Database session
        output_dir: Output directory (e.g., ./data/decision_traces/)
        window_days: Time window to export (default 30)
    
    Returns:
        List of exported file paths
    """
    logger.info(f"Exporting all decision traces (window={window_days}d)")

    # Get all users
    users = session.query(User).all()

    if not users:
        logger.warning("No users found in database")
        return []

    exported_paths = []

    for user in users:
        try:
            path = export_decision_trace(
                user.user_id,
                window_days,
                session,
                output_dir,
            )
            exported_paths.append(path)
        except Exception as e:
            logger.error(f"Error exporting trace for {user.user_id}: {e}")
            continue

    logger.info(f"Exported {len(exported_paths)} decision traces to {output_dir}")
    return exported_paths

