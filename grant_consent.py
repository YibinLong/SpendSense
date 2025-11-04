#!/usr/bin/env python3
"""
Grant consent for all users in the database.

This is a helper script for development/testing to allow all users
to access their profiles and recommendations without manually granting consent.
"""

from datetime import datetime

from spendsense.app.db.session import get_session, init_db
from spendsense.app.db.models import User, ConsentEvent


def grant_all_consent():
    """Grant consent for all users."""
    init_db()
    
    with next(get_session()) as session:
        # Get all users
        users = session.query(User).all()
        
        print(f"Granting consent for {len(users)} users...")
        
        for user in users:
            # Check if user already has consent
            existing_consent = session.query(ConsentEvent).filter(
                ConsentEvent.user_id == user.user_id,
                ConsentEvent.action == "opt_in"
            ).first()
            
            if existing_consent:
                print(f"  ✓ {user.user_id} already has consent")
                continue
            
            # Create consent event
            consent = ConsentEvent(
                user_id=user.user_id,
                action="opt_in",
                reason="Development/testing auto-consent",
                consent_given_by="system",
                timestamp=datetime.utcnow()
            )
            session.add(consent)
            print(f"  ✓ Granted consent for {user.user_id}")
        
        session.commit()
        print(f"\n✅ Consent granted for all users!")


if __name__ == "__main__":
    grant_all_consent()

