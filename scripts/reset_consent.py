"""
Reset all users' consent to opt_out.

This script resets all consent for all users by creating opt_out consent events.

Why this exists:
- To implement the requirement that users start without consent
- Users must explicitly opt-in before viewing insights
- Provides a clean slate for testing consent flow

Usage:
    python -m scripts.reset_consent
"""

from scripts._bootstrap import add_project_root

add_project_root()

from datetime import datetime

from sqlalchemy.orm import Session

from spendsense.app.core.logging import configure_logging, get_logger
from spendsense.app.db.models import ConsentEvent, User
from spendsense.app.db.session import get_session

configure_logging(debug=True)
logger = get_logger(__name__)


def reset_all_consent():
    """Reset consent for all users to opt_out."""
    logger.info("starting_consent_reset")
    
    with next(get_session()) as session:
        # Get all users
        users = session.query(User).all()
        logger.info(f"found_{len(users)}_users")
        
        reset_count = 0
        for user in users:
            # Create an opt_out consent event for each user
            consent_event = ConsentEvent(
                user_id=user.user_id,
                action="opt_out",
                reason="Initial consent reset - users must opt-in to view insights",
                consent_given_by="reset_consent_script",
                timestamp=datetime.utcnow(),
            )
            session.add(consent_event)
            reset_count += 1
            logger.info(f"reset_consent_for_user", user_id=user.user_id)
        
        # Commit all changes
        session.commit()
        logger.info(f"consent_reset_complete", reset_count=reset_count)
        
        print(f"\n✅ Reset consent for {reset_count} users")
        print("All users now have opt_out consent status")
        print("Users must grant consent to view insights")


if __name__ == "__main__":
    reset_all_consent()
