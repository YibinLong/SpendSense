"""
Tone checking for recommendation rationales.

This module ensures all recommendation rationales use supportive, non-shaming language.

Why this exists:
- PRD requires no shaming language in any recommendation
- Automated checks catch problematic phrasing before showing to users
- Dev mode logging helps debug rejected rationales

Hybrid approach:
1. Keyword blocklist - catches obvious negative/shaming words
2. Positive phrasing rules - ensures supportive language is present
"""

import re

from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger

logger = get_logger(__name__)


# Blocklist of shaming/negative words that should never appear
SHAMING_KEYWORDS = [
    "lazy",
    "irresponsible",
    "wasteful",
    "bad at money",
    "poor choices",
    "foolish",
    "stupid",
    "reckless",
    "careless",
    "incompetent",
    "bad financial habits",
    "spending problem",
    "can't manage",
    "failing to",
    "you should have",
    "you must",
    "you need to stop",
]

# Absolute/judgmental phrases to avoid
ABSOLUTE_PHRASES = [
    "you always",
    "you never",
    "everyone knows",
    "obviously",
    "clearly you",
]

# Supportive words that should be present
SUPPORTIVE_WORDS = [
    "consider",
    "might",
    "could",
    "opportunity",
    "next step",
    "small change",
    "progress",
    "improve",
    "optimize",
    "help",
    "support",
    "guide",
    "suggest",
    "recommend",
    "option",
    "choice",
]


def check_tone(text: str) -> tuple[bool, list[str]]:
    """
    Check if text uses supportive, non-shaming tone.
    
    How it works:
    1. Check for blocklisted shaming keywords
    2. Check for absolute/judgmental phrases
    3. Verify at least one supportive word is present
    4. Return pass/fail with specific issues found
    
    Why hybrid approach:
    - Keywords catch obvious problems (fast, deterministic)
    - Positive phrasing ensures recommendations are constructive
    - No LLM needed, runs instantly
    
    Args:
        text: The rationale or recommendation text to check
    
    Returns:
        Tuple of (passed: bool, issues: list[str])
        - passed: True if tone check passes
        - issues: List of specific problems found (empty if passed)
    
    Example:
        passed, issues = check_tone("You're irresponsible with money")
        # passed = False
        # issues = ["Contains shaming keyword: irresponsible"]
        
        passed, issues = check_tone("Consider paying more than the minimum")
        # passed = True
        # issues = []
    """
    issues: list[str] = []
    text_lower = text.lower()

    # Check for shaming keywords
    for keyword in SHAMING_KEYWORDS:
        if keyword.lower() in text_lower:
            issues.append(f"Contains shaming keyword: {keyword}")

    # Check for absolute phrases
    for phrase in ABSOLUTE_PHRASES:
        if phrase.lower() in text_lower:
            issues.append(f"Contains absolute/judgmental phrase: {phrase}")

    # Check for at least one supportive word
    has_supportive = any(
        word.lower() in text_lower
        for word in SUPPORTIVE_WORDS
    )

    if not has_supportive:
        issues.append("Missing supportive language (should contain words like: consider, might, could, opportunity)")

    # Check for excessive exclamation marks (can feel aggressive)
    exclamation_count = text.count("!")
    if exclamation_count > 1:
        issues.append(f"Too many exclamation marks ({exclamation_count}), use at most 1")

    # Check for all caps (can feel like shouting)
    if re.search(r'\b[A-Z]{4,}\b', text):
        issues.append("Contains all-caps words (avoid shouting)")

    passed = len(issues) == 0

    # Log rejections in dev mode
    if not passed and settings.is_dev:
        logger.warning(
            "tone_check_failed",
            text=text[:100],  # First 100 chars
            issues=issues,
        )

    if passed:
        logger.debug("tone_check_passed", text=text[:50])

    return passed, issues


def suggest_tone_fix(text: str, issues: list[str]) -> str:
    """
    Suggest a tone-friendly version of text.
    
    This provides automated suggestions for fixing tone issues.
    Used in dev mode to help content creators.
    
    Args:
        text: Original text that failed tone check
        issues: List of issues from check_tone()
    
    Returns:
        Suggested alternative text (or original if no suggestions)
    """
    suggestions: list[str] = []

    # Replace shaming keywords with neutral alternatives
    replacements = {
        "irresponsible": "could be optimized",
        "lazy": "opportunity to automate",
        "wasteful": "opportunity to reduce",
        "bad at money": "developing financial skills",
        "poor choices": "areas to improve",
        "foolish": "opportunity to reconsider",
        "reckless": "aggressive",
        "careless": "worth reviewing",
        "you should have": "consider",
        "you must": "you might",
        "you need to stop": "consider reducing",
        "you always": "frequently",
        "you never": "rarely",
    }

    suggested_text = text
    for bad_word, good_word in replacements.items():
        suggested_text = re.sub(
            bad_word,
            good_word,
            suggested_text,
            flags=re.IGNORECASE
        )

    # Add supportive opener if missing
    if "Missing supportive language" in str(issues):
        suggested_text = f"Consider this: {suggested_text}"

    return suggested_text


