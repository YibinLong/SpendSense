"""
Recommendation engine for SpendSense.

This module generates personalized education and offer recommendations
based on user personas and behavioral signals.

Why this exists:
- Central logic for building recommendations with rationales
- Combines persona, signals, content catalog, eligibility, and tone checks
- Ensures every recommendation has concrete data-driven rationale
- Persists recommendations with guardrail decisions for operator review
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    Recommendation,
    SubscriptionSignal,
    SavingsSignal,
    CreditSignal,
    IncomeSignal,
    Persona,
    Liability,
)
from spendsense.app.recommend.eligibility import check_eligibility, validate_offer_safety
from spendsense.app.recommend.tone import check_tone
from spendsense.app.recommend.disclosure import add_disclosure
from spendsense.app.schemas.recommendation import RecommendationItem


logger = get_logger(__name__)


def load_content_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load the content catalog JSON file.
    
    Returns:
        Dict with 'education_items' and 'partner_offers' lists
    """
    catalog_path = Path(__file__).parent / "content_catalog.json"
    
    try:
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
        logger.debug("content_catalog_loaded", item_count=len(catalog.get("education_items", [])) + len(catalog.get("partner_offers", [])))
        return catalog
    except Exception as e:
        logger.error("failed_to_load_catalog", error=str(e))
        return {"education_items": [], "partner_offers": []}


def build_rationale(
    item: Dict[str, Any],
    persona_id: str,
    signals: Dict[str, Any],
) -> str:
    """
    Build a plain-language rationale citing concrete signal data.
    
    This is the heart of explainability - we tell users WHY they're seeing
    this recommendation using their actual transaction data.
    
    Args:
        item: The content item from catalog
        persona_id: The user's assigned persona
        signals: Dict with all signal data
    
    Returns:
        Plain-language rationale string
    
    Example:
        "Your utilization is 68% on card ending in 4523. Consider paying more 
        than the minimum to reduce interest charges and improve your credit score."
    """
    rationale_parts = []
    
    # Persona-specific rationale builders
    if persona_id == "high_utilization":
        credit = signals.get("credit", {})
        max_util = credit.get("credit_utilization_max_pct", 0)
        has_interest = credit.get("has_interest_charges", False)
        is_overdue = credit.get("is_overdue", False)
        
        if max_util > 0:
            rationale_parts.append(f"Your credit utilization is {max_util}%")
        if has_interest:
            rationale_parts.append("you're paying interest charges")
        if is_overdue:
            rationale_parts.append("you have overdue payments")
        
        rationale_parts.append("Consider this resource to help reduce your credit burden")
    
    elif persona_id == "variable_income_budgeter":
        income = signals.get("income", {})
        pay_gap = income.get("median_pay_gap_days", 0)
        buffer = income.get("cashflow_buffer_months", 0)
        
        rationale_parts.append(f"Your paychecks arrive every {pay_gap} days on average")
        rationale_parts.append(f"with a {buffer:.1f} month cash-flow buffer")
        rationale_parts.append("This resource might help you manage irregular income")
    
    elif persona_id == "subscription_heavy":
        subscription = signals.get("subscription", {})
        merchant_count = subscription.get("recurring_merchant_count", 0)
        monthly_spend = subscription.get("monthly_recurring_spend", 0)
        
        rationale_parts.append(f"You have {merchant_count} recurring subscriptions")
        rationale_parts.append(f"totaling about ${monthly_spend}/month")
        rationale_parts.append("Consider this resource to help optimize your subscriptions")
    
    elif persona_id == "savings_builder":
        savings = signals.get("savings", {})
        growth = savings.get("savings_growth_rate_pct", 0)
        inflow = savings.get("savings_net_inflow", 0)
        
        if growth > 0:
            rationale_parts.append(f"Your savings grew {growth}% this period")
        if inflow > 0:
            rationale_parts.append(f"with ${inflow:.2f}/month in new deposits")
        rationale_parts.append("This resource could help you optimize your savings strategy")
    
    elif persona_id == "cash_flow_optimizer":
        income = signals.get("income", {})
        buffer = income.get("cashflow_buffer_months", 0)
        
        rationale_parts.append(f"Your cash-flow buffer is {buffer:.1f} months")
        rationale_parts.append("suggesting opportunity for short-term optimization")
        rationale_parts.append("This resource might help you improve your cash flow")
    
    else:
        # Generic rationale
        rationale_parts.append("Based on your financial profile")
        rationale_parts.append("this resource might be helpful")
    
    return ". ".join(rationale_parts) + "."


def generate_recommendations(
    user_id: str,
    window_days: int,
    session: Session,
) -> List[RecommendationItem]:
    """
    Generate personalized recommendations for a user.
    
    How it works:
    1. Load persona for user+window
    2. Load all signals
    3. Load content catalog
    4. Filter items by persona tags
    5. Check eligibility for offers
    6. Build rationale using concrete signal data
    7. Apply tone check to rationale
    8. Add disclosure
    9. Store to Recommendation table
    10. Return 3-5 education + 1-3 offers
    
    Args:
        user_id: User identifier
        window_days: Time window in days (30 or 180)
        session: SQLAlchemy database session
    
    Returns:
        List of RecommendationItem objects
    
    Example:
        recommendations = generate_recommendations("user_123", 30, session)
        # Returns 4-8 items with rationales and disclosures
    """
    logger.info(
        "generating_recommendations",
        user_id=user_id,
        window_days=window_days,
    )
    
    # Load persona
    persona = session.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window_days,
    ).first()
    
    if not persona:
        logger.warning("no_persona_found", user_id=user_id, window_days=window_days)
        return []
    
    persona_id = persona.persona_id
    
    # Load all signals
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
    
    # Build signals dict for eligibility and rationale
    signals = {
        "subscription": {
            "recurring_merchant_count": subscription_signal.recurring_merchant_count if subscription_signal else 0,
            "monthly_recurring_spend": subscription_signal.monthly_recurring_spend if subscription_signal else Decimal("0"),
            "subscription_share_pct": subscription_signal.subscription_share_pct if subscription_signal else Decimal("0"),
        } if subscription_signal else {},
        "savings": {
            "savings_net_inflow": savings_signal.savings_net_inflow if savings_signal else Decimal("0"),
            "savings_growth_rate_pct": savings_signal.savings_growth_rate_pct if savings_signal else Decimal("0"),
            "emergency_fund_months": savings_signal.emergency_fund_months if savings_signal else Decimal("0"),
        } if savings_signal else {},
        "credit": {
            "credit_utilization_max_pct": credit_signal.credit_utilization_max_pct if credit_signal else Decimal("0"),
            "credit_utilization_avg_pct": credit_signal.credit_utilization_avg_pct if credit_signal else Decimal("0"),
            "credit_util_flag_30": credit_signal.credit_util_flag_30 if credit_signal else False,
            "credit_util_flag_50": credit_signal.credit_util_flag_50 if credit_signal else False,
            "has_interest_charges": credit_signal.has_interest_charges if credit_signal else False,
            "is_overdue": credit_signal.is_overdue if credit_signal else False,
        } if credit_signal else {},
        "income": {
            "payroll_deposit_count": income_signal.payroll_deposit_count if income_signal else 0,
            "median_pay_gap_days": income_signal.median_pay_gap_days if income_signal else Decimal("0"),
            "cashflow_buffer_months": income_signal.cashflow_buffer_months if income_signal else Decimal("0"),
        } if income_signal else {},
    }
    
    # Load content catalog
    catalog = load_content_catalog()
    
    # Filter items by persona tags
    education_candidates = [
        item for item in catalog.get("education_items", [])
        if persona_id in item.get("tags", [])
    ]
    
    offer_candidates = [
        item for item in catalog.get("partner_offers", [])
        if persona_id in item.get("tags", [])
    ]
    
    logger.debug(
        "candidates_filtered",
        persona_id=persona_id,
        education_count=len(education_candidates),
        offer_count=len(offer_candidates),
    )
    
    # Build final recommendations
    recommendations = []
    
    # Process education items (target 3-5)
    for item in education_candidates[:5]:
        rationale = build_rationale(item, persona_id, signals)
        
        # Tone check
        tone_passed, tone_issues = check_tone(rationale)
        if not tone_passed:
            logger.warning(
                "rationale_tone_failed",
                item_id=item["id"],
                issues=tone_issues,
            )
            continue  # Skip this item
        
        # Add disclosure
        item_with_disclosure = add_disclosure(item)
        
        # Create recommendation record
        rec = Recommendation(
            user_id=user_id,
            persona_id=persona_id,
            item_type="education",
            title=item["title"],
            rationale=rationale,
            eligibility_flags=json.dumps({"tone_check": "passed"}),
            disclosure=item_with_disclosure["disclosure"],
            status="pending",
        )
        session.add(rec)
        recommendations.append(rec)
    
    # Process offers (target 1-3)
    for item in offer_candidates[:3]:
        # Safety check
        if not validate_offer_safety(item):
            logger.warning("offer_blocked_unsafe", item_id=item["id"])
            continue
        
        # Eligibility check
        eligible, eligibility_reason = check_eligibility(item, signals)
        if not eligible:
            logger.debug(
                "offer_filtered_ineligible",
                item_id=item["id"],
                reason=eligibility_reason,
            )
            continue
        
        rationale = build_rationale(item, persona_id, signals)
        
        # Tone check
        tone_passed, tone_issues = check_tone(rationale)
        if not tone_passed:
            logger.warning(
                "rationale_tone_failed",
                item_id=item["id"],
                issues=tone_issues,
            )
            continue
        
        # Add disclosure
        item_with_disclosure = add_disclosure(item)
        
        # Create recommendation record
        rec = Recommendation(
            user_id=user_id,
            persona_id=persona_id,
            item_type="offer",
            title=item["title"],
            rationale=rationale,
            eligibility_flags=json.dumps({
                "eligible": True,
                "reason": eligibility_reason,
                "tone_check": "passed",
            }),
            disclosure=item_with_disclosure["disclosure"],
            status="pending",
        )
        session.add(rec)
        recommendations.append(rec)
    
    # Commit all recommendations
    session.commit()
    
    # Refresh and convert to schemas
    result = []
    for rec in recommendations:
        session.refresh(rec)
        result.append(RecommendationItem.model_validate(rec))
    
    logger.info(
        "recommendations_generated",
        user_id=user_id,
        window_days=window_days,
        persona_id=persona_id,
        education_count=len([r for r in result if r.item_type == "education"]),
        offer_count=len([r for r in result if r.item_type == "offer"]),
    )
    
    return result

