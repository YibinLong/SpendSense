#!/usr/bin/env python3
"""
Complete database reset and population script.

This script:
1. Drops all existing tables and data
2. Creates fresh tables
3. Seeds database with users, accounts, transactions
4. Runs feature engineering pipeline for ALL users
5. Ensures every user has signals, personas, and recommendations

Usage:
    python reset_and_populate.py
"""

from spendsense.app.db.session import drop_all_tables, init_db, get_session
from spendsense.app.db.seed import seed_database
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
    """Reset database and populate with complete data."""
    print("=" * 70)
    print("DATABASE RESET AND POPULATION")
    print("=" * 70)
    print()
    
    # Step 1: Drop all tables
    print("Step 1: Dropping all existing tables and data...")
    drop_all_tables()
    print("✓ All tables dropped")
    print()
    
    # Step 2: Create fresh tables
    print("Step 2: Creating fresh database tables...")
    init_db()
    print("✓ Database initialized")
    print()
    
    # Step 3: Seed with users, accounts, transactions
    print("Step 3: Seeding database with users, accounts, and transactions...")
    print("  - Creating 25 users (5 per persona)")
    print("  - Creating 2-4 accounts per user")
    print("  - Creating 180 days of transaction history")
    seed_database()
    print("✓ Database seeded with persona-labeled users")
    print()
    
    # Step 4: Run feature engineering for ALL users
    print("Step 4: Running feature engineering pipeline for ALL users...")
    print("  - Computing behavioral signals (30d and 180d windows)")
    print("  - Assigning personas")
    print("  - Generating recommendations")
    print()
    
    with next(get_session()) as session:
        # Get ALL users
        users = session.query(User).all()
        total_users = len(users)
        
        logger.info(f"Processing {total_users} users")
        print(f"Processing {total_users} users...")
        print()
        
        # Store user_id separately to avoid session issues after rollback
        user_ids = [user.user_id for user in users]
        
        successful = 0
        failed = 0
        
        for idx, user_id in enumerate(user_ids, 1):
            print(f"[{idx}/{total_users}] Processing {user_id}...", end=" ")
            
            for window_days in [30, 180]:
                try:
                    # Step 1: Compute and store signals
                    compute_and_store_signals(user_id, window_days, session)
                    
                    # Step 2: Assign persona
                    persona = assign_persona(user_id, window_days, session)
                    
                    # Step 3: Generate recommendations
                    recommendations = generate_recommendations(
                        user_id, window_days, session
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Error processing {user_id} (window={window_days}d): {e}"
                    )
                    session.rollback()
                    failed += 1
                    print(f"❌ FAILED ({e})")
                    break
            else:
                # Only executed if loop completed without break
                successful += 1
                print("✓")
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total users:       {total_users}")
    print(f"Successfully processed: {successful}")
    print(f"Failed:            {failed}")
    print()
    
    if successful == total_users:
        print("🎉 SUCCESS! All users have complete data:")
        print("   ✓ Behavioral signals (30d and 180d windows)")
        print("   ✓ Assigned personas")
        print("   ✓ Personalized recommendations")
        print()
        print("👉 Refresh your browser to see the populated data!")
    else:
        print(f"⚠️  Warning: {failed} users failed to process")
    
    print()


if __name__ == "__main__":
    main()

