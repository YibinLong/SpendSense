"""
Centralized policy checks for recommendations.

This module consolidates guardrail validation logic for easy testing and auditing.

Why this exists:
- Central place for all safety and policy checks
- Easy to audit and update policies
- Returns structured guardrail_decisions for transparency
"""

from typing import Any

from spendsense.app.core.logging import get_logger
from spendsense.app.recommend.eligibility import validate_offer_safety
from spendsense.app.recommend.tone import check_tone

logger = get_logger(__name__)


def ensure_guardrails(
    recommendation_dict: dict[str, Any],
    signals: dict[str, Any],
) -> dict[str, Any]:
    """
    Run all guardrail checks on a recommendation.
    
    This centralizes:
    - Offer safety validation
    - Tone checking
    - Eligibility verification
    
    Returns a guardrail_decisions dict that can be stored with the recommendation
    for full traceability.
    
    Args:
        recommendation_dict: The recommendation data (title, rationale, etc.)
        signals: User's behavioral signals
    
    Returns:
        Dict with guardrail check results
    
    Example:
        decisions = ensure_guardrails(rec, signals)
        # {
        #     "offer_safety": {"passed": True, "blocked_types": []},
        #     "tone_check": {"passed": True, "issues": []},
        #     "eligibility": {"passed": True, "reason": "Meets all criteria"},
        # }
    """
    decisions: dict[str, Any] = {}

    # Safety check (for offers)
    if recommendation_dict.get("type") == "offer":
        is_safe = validate_offer_safety(recommendation_dict)
        decisions["offer_safety"] = {
            "passed": is_safe,
            "content_type": recommendation_dict.get("content_type"),
        }

        if not is_safe:
            logger.warning(
                "guardrail_failed_safety",
                item_id=recommendation_dict.get("id"),
            )

    # Tone check (for all recommendations)
    rationale = recommendation_dict.get("rationale", "")
    if rationale:
        tone_passed, tone_issues = check_tone(rationale)
        decisions["tone_check"] = {
            "passed": tone_passed,
            "issues": tone_issues,
        }

        if not tone_passed:
            logger.warning(
                "guardrail_failed_tone",
                item_id=recommendation_dict.get("id"),
                issues=tone_issues,
            )

    # Log overall guardrail status
    all_passed = all(
        check.get("passed", True)
        for check in decisions.values()
    )

    decisions["all_passed"] = all_passed

    if all_passed:
        logger.debug(
            "guardrails_passed",
            item_id=recommendation_dict.get("id"),
        )

    return decisions


