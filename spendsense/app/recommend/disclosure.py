"""
Disclosure text management for recommendations.

This module appends mandatory educational disclaimers to all recommendations.

Why this exists:
- PRD requires clear disclosure that content is educational, not advice
- Consistent disclaimer across all recommendation types
- Legal protection and user transparency
"""

from spendsense.app.core.logging import get_logger


logger = get_logger(__name__)


# Mandatory disclosure text from PRD
EDUCATIONAL_DISCLAIMER = (
    "This is educational content, not financial advice. "
    "Consult a licensed advisor for personalized guidance."
)


def add_disclosure(recommendation_data: dict) -> dict:
    """
    Add mandatory educational disclaimer to a recommendation.
    
    How it works:
    - Appends EDUCATIONAL_DISCLAIMER to the recommendation dict
    - Returns modified dict (doesn't mutate original)
    - Logs when disclosure is added
    
    Why we need this:
    - PRD requirement for all recommendations
    - Protects users and SpendSense from liability
    - Makes it clear this is education, not financial advice
    
    Args:
        recommendation_data: Dict with recommendation fields
    
    Returns:
        Dict with disclosure field added
    
    Example:
        rec = {"title": "Pay down credit cards", "rationale": "..."}
        rec_with_disclosure = add_disclosure(rec)
        # rec_with_disclosure["disclosure"] = "This is educational content..."
    """
    # Make a copy to avoid mutating the original
    result = recommendation_data.copy()
    
    # Add disclosure if not already present
    if "disclosure" not in result or not result["disclosure"]:
        result["disclosure"] = EDUCATIONAL_DISCLAIMER
        logger.debug(
            "disclosure_added",
            item_id=result.get("id"),
            item_type=result.get("type"),
        )
    
    return result


def get_disclosure() -> str:
    """
    Get the standard educational disclaimer text.
    
    Returns:
        The mandatory disclosure text
    """
    return EDUCATIONAL_DISCLAIMER

