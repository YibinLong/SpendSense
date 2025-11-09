"""
Eligibility checking for partner offers.

This module filters out offers that users aren't eligible for,
blocking predatory products and enforcing minimum requirements.

Why this exists:
- PRD requires eligibility checks on all partner offers
- Prevents showing irrelevant offers that would be denied
- Blocks harmful products (payday loans, predatory offers)
- Provides clear reasons when offers are filtered out
"""

from decimal import Decimal
from typing import Any

from spendsense.app.core.logging import get_logger

logger = get_logger(__name__)


# Predatory product types that are always blocked
BLOCKED_PRODUCT_TYPES = [
    "payday_loan",
    "title_loan",
    "pawn_loan",
    "rent_to_own",
]


def check_eligibility(
    item: dict[str, Any],
    signals: dict[str, Any],
    user_data: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """
    Check if a user is eligible for a partner offer.
    
    How it works:
    1. Check for predatory product types (always blocked)
    2. Check minimum income requirements if specified
    3. Check credit utilization thresholds
    4. Check other criteria from eligibility_criteria field
    5. Return eligible/not eligible with reason
    
    Why we need this:
    - Shows only relevant offers
    - Protects users from predatory products
    - Provides transparency about why offers are shown/hidden
    
    Args:
        item: The offer dict from content_catalog.json
        signals: Dict with all 4 signal types (credit, income, savings, subscription)
        user_data: Optional additional user data (age, income, etc.)
    
    Returns:
        Tuple of (eligible: bool, reason: str)
        - eligible: True if user meets all criteria
        - reason: Explanation of eligibility decision
    
    Example:
        eligible, reason = check_eligibility(
            item={"eligibility_criteria": {"min_credit_score": 670}},
            signals={"credit": {"utilization_max": 45}},
            user_data={"credit_score": 700}
        )
        # eligible = True
        # reason = "Meets all eligibility criteria"
    """
    eligibility_criteria = item.get("eligibility_criteria", {})
    item_type = item.get("content_type", "unknown")

    # Block savings-account offers when user already has a savings account
    # PRD: "Filter based on existing accounts (don't offer savings account if they have one)"
    if item_type == "savings_account":
        has_savings_account = False
        if user_data and isinstance(user_data, dict):
            has_savings_account = bool(user_data.get("has_savings_account"))
        if has_savings_account:
            logger.info(
                "offer_blocked_existing_savings",
                item_id=item.get("id"),
                content_type=item_type,
            )
            return False, "User already has a savings account"

    # Block predatory products
    if item_type in BLOCKED_PRODUCT_TYPES:
        logger.info(
            "offer_blocked_predatory",
            item_id=item.get("id"),
            content_type=item_type,
        )
        return False, f"Product type '{item_type}' is not permitted"

    # If no criteria specified, offer is eligible
    if not eligibility_criteria:
        return True, "No eligibility restrictions"

    # Check minimum credit score
    if "min_credit_score" in eligibility_criteria:
        min_score = eligibility_criteria["min_credit_score"]
        user_score = user_data.get("credit_score") if user_data else None

        if user_score is None:
            logger.debug(
                "eligibility_check_skipped",
                item_id=item.get("id"),
                reason="Credit score not available",
            )
            # If we don't have score data, we can't check - be conservative
            return False, "Credit score data not available for verification"

        if user_score < min_score:
            return False, f"Requires credit score ≥{min_score}"

    # Check maximum utilization
    if "max_utilization" in eligibility_criteria:
        max_util = Decimal(str(eligibility_criteria["max_utilization"]))
        credit_data = signals.get("credit", {})
        current_util = credit_data.get("credit_utilization_max_pct", Decimal("0"))

        if current_util > max_util:
            return False, f"Credit utilization too high (maximum {max_util}%)"

    # Check not overdue requirement
    if eligibility_criteria.get("not_overdue", False):
        credit_data = signals.get("credit", {})
        is_overdue = credit_data.get("is_overdue", False)

        if is_overdue:
            return False, "Cannot have overdue payments"

    # Check minimum age
    if "min_age" in eligibility_criteria:
        min_age = eligibility_criteria["min_age"]
        user_age = user_data.get("age") if user_data else None

        if user_age is None:
            # Age not available, can't verify
            return False, "Age verification required"

        if user_age < min_age:
            return False, f"Requires age ≥{min_age}"

    # Check minimum monthly bills (for bill negotiation services)
    if "min_monthly_bills" in eligibility_criteria:
        min_bills = Decimal(str(eligibility_criteria["min_monthly_bills"]))
        subscription_data = signals.get("subscription", {})
        monthly_recurring = subscription_data.get("monthly_recurring_spend", Decimal("0"))

        if monthly_recurring < min_bills:
            return False, f"Requires at least ${min_bills}/month in recurring bills"

    # All checks passed
    logger.debug(
        "offer_eligible",
        item_id=item.get("id"),
        criteria_checked=list(eligibility_criteria.keys()),
    )
    return True, "Meets all eligibility criteria"


def validate_offer_safety(item: dict[str, Any]) -> bool:
    """
    Validate that an offer is safe and not predatory.
    
    This is a stricter check than eligibility - it's about whether
    we should EVER show this offer type, regardless of user criteria.
    
    Args:
        item: The offer dict from content_catalog.json
    
    Returns:
        True if offer is safe, False if predatory
    """
    item_type = item.get("content_type", "unknown")

    # Block predatory product types
    if item_type in BLOCKED_PRODUCT_TYPES:
        return False

    # Block offers with excessive fees (if specified)
    if "fee_percentage" in item.get("eligibility_criteria", {}):
        fee_pct = item["eligibility_criteria"]["fee_percentage"]
        if fee_pct > 10:  # More than 10% fee is predatory
            return False

    # Block high APR offers (if specified)
    if "apr" in item.get("eligibility_criteria", {}):
        apr = item["eligibility_criteria"]["apr"]
        if apr > 36:  # More than 36% APR is predatory
            return False

    return True


