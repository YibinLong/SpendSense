#!/usr/bin/env python3
"""
Run feature engineering, persona assignment, and recommendation generation pipelines.

This script computes signals, assigns personas, and generates recommendations 
for all users in the database.
"""

from scripts._bootstrap import add_project_root

add_project_root()

from datetime import datetime
from spendsense.app.db.session import get_session
from spendsense.app.db.models import (
    User, SubscriptionSignal, SavingsSignal, CreditSignal, IncomeSignal,
    Persona, Recommendation
)
from spendsense.app.features import credit, income, savings, subscriptions
from spendsense.app.personas.assign import assign_persona
from spendsense.app.recommend.engine import generate_recommendations
from spendsense.app.core.logging import get_logger


logger = get_logger(__name__)


def delete_existing_signals(user_id: str, window_days: int, session):
    """Delete existing signals for a user and window to avoid unique constraint errors."""
    logger.debug(f"Deleting existing signals for {user_id} (window={window_days}d)")
    
    # Delete existing signals
    session.query(SubscriptionSignal).filter(
        SubscriptionSignal.user_id == user_id,
        SubscriptionSignal.window_days == window_days
    ).delete()
    
    session.query(SavingsSignal).filter(
        SavingsSignal.user_id == user_id,
        SavingsSignal.window_days == window_days
    ).delete()
    
    session.query(CreditSignal).filter(
        CreditSignal.user_id == user_id,
        CreditSignal.window_days == window_days
    ).delete()
    
    session.query(IncomeSignal).filter(
        IncomeSignal.user_id == user_id,
        IncomeSignal.window_days == window_days
    ).delete()
    
    # Delete existing persona
    session.query(Persona).filter(
        Persona.user_id == user_id,
        Persona.window_days == window_days
    ).delete()
    
    # Delete existing recommendations
    session.query(Recommendation).filter(
        Recommendation.user_id == user_id,
        Recommendation.window_days == window_days
    ).delete()
    
    session.commit()
    logger.debug(f"Existing data deleted for {user_id} (window={window_days}d)")


def compute_and_store_signals(user_id: str, window_days: int, session):
    """Compute all signals for a user and store them in the database."""
    logger.info(f"Computing signals for {user_id} (window={window_days}d)")
    
    # Delete existing signals first to avoid unique constraint errors
    delete_existing_signals(user_id, window_days, session)
    
    # Compute subscription signals
    subscription_signal = subscriptions.compute_subscription_signals(
        user_id, window_days, session
    )
    session.add(subscription_signal)
    
    # Compute savings signals
    savings_signal = savings.compute_savings_signals(
        user_id, window_days, session
    )
    session.add(savings_signal)
    
    # Compute credit signals
    credit_signal = credit.compute_credit_signals(
        user_id, window_days, session
    )
    session.add(credit_signal)
    
    # Compute income signals
    income_signal = income.compute_income_signals(
        user_id, window_days, session
    )
    session.add(income_signal)
    
    session.commit()
    logger.info(f"Signals computed for {user_id}")


def main():
    """Run the complete pipeline for all users."""
    logger.info("Starting pipeline execution")
    
    with next(get_session()) as session:
        # Get all users
        users = session.query(User).limit(10).all()  # Process first 10 users for demo
        
        logger.info(f"Processing {len(users)} users")
        
        # Store user_id separately to avoid session issues after rollback
        user_ids = [user.user_id for user in users]
        
        for user_id in user_ids:
            logger.info(f"Processing user: {user_id}")
            
            for window_days in [30, 180]:
                try:
                    # Step 1: Compute and store signals
                    compute_and_store_signals(user_id, window_days, session)
                    
                    # Step 2: Assign persona
                    persona = assign_persona(user_id, window_days, session)
                    logger.info(
                        f"Assigned persona: {persona.persona_id} "
                        f"(user={user_id}, window={window_days}d)"
                    )
                    
                    # Step 3: Generate recommendations
                    recommendations = generate_recommendations(
                        user_id, window_days, session
                    )
                    logger.info(
                        f"Generated {len(recommendations)} recommendations "
                        f"(user={user_id}, window={window_days}d)"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Error processing {user_id} (window={window_days}d): {e}"
                    )
                    session.rollback()
                    continue
        
        logger.info("Pipeline execution complete")


if __name__ == "__main__":
    main()
