"""
Synthetic data generation for SpendSense.

This module generates realistic fake financial data for testing.

Why this exists:
- Need test data without real PII
- Must cover all persona patterns (subscriptions, high utilization, etc.)
- Deterministic generation (uses SEED from config)
- Generates 50 users with complete financial profiles

Usage:
    from spendsense.app.db.session import init_db
    from spendsense.app.db.seed import seed_database
    
    init_db()
    seed_database()
"""

import csv
import json
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from spendsense.app.auth.password import hash_password
from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    Account,
    ConsentEvent,
    Liability,
    Transaction,
    User,
)
from spendsense.app.db.session import get_session
from spendsense.app.schemas.account import AccountCreate
from spendsense.app.schemas.consent_event import ConsentEventCreate
from spendsense.app.schemas.liability import LiabilityCreate
from spendsense.app.schemas.transaction import TransactionCreate
from spendsense.app.schemas.user import UserCreate

logger = get_logger(__name__)


# Set random seed for deterministic generation
random.seed(settings.seed)


# Merchant lists for different categories (realistic patterns)
SUBSCRIPTION_MERCHANTS = [
    "Netflix", "Spotify", "Disney+", "Hulu", "Amazon Prime",
    "Apple Music", "YouTube Premium", "Planet Fitness", "LA Fitness",
    "Adobe Creative Cloud", "Microsoft 365", "Dropbox", "iCloud Storage"
]

GROCERY_MERCHANTS = [
    "Whole Foods", "Trader Joe's", "Safeway", "Kroger", "Walmart Grocery",
    "Target", "Costco", "Sprouts", "Publix"
]

DINING_MERCHANTS = [
    "Chipotle", "Starbucks", "McDonald's", "Subway", "Panera Bread",
    "Olive Garden", "The Cheesecake Factory", "PF Chang's", "Outback Steakhouse"
]

SHOPPING_MERCHANTS = [
    "Amazon", "Target", "Walmart", "Best Buy", "Home Depot",
    "Lowe's", "IKEA", "Macy's", "Nordstrom", "Gap"
]

UTILITY_MERCHANTS = [
    "PG&E Electric", "Comcast Internet", "AT&T Wireless", "Verizon Wireless",
    "T-Mobile", "Water Company", "Waste Management"
]


# Friendly labels to make demo users easy to recognize in the UI
# These are stored in the email_masked field purely as a display label
# so it is obvious what behavior/persona to expect when testing.
FRIENDLY_USER_LABELS = [
    "Sam Subscriber — Subscription-heavy",
    "Sally Saver — Savings builder",
    "Harry HighUtil — High credit utilization",
    "Ivy Irregular — Variable income",
    "Paula PayMin — Minimum payments only",
    "Owen Overdue — Overdue risk",
    "Gina Groceries — Grocery spender",
    "Dina Dining — Eats out often",
    "Cathy CashBuffer — Strong cash buffer",
    "Manny Minimalist — Low activity",
]


def generate_user_id(index: int) -> str:
    """Generate masked user ID."""
    return f"usr_{str(index).zfill(6)}"


def generate_account_id(user_index: int, account_index: int) -> str:
    """Generate masked account ID."""
    return f"acc_{str(user_index).zfill(6)}_{str(account_index).zfill(2)}"


def generate_transaction_id(user_index: int, account_index: int, tx_index: int) -> str:
    """Generate unique transaction ID."""
    return f"txn_{str(user_index).zfill(6)}_{str(account_index).zfill(2)}_{str(tx_index).zfill(4)}"


def generate_liability_id(user_index: int, liability_index: int) -> str:
    """Generate liability ID."""
    return f"liab_{str(user_index).zfill(6)}_{str(liability_index).zfill(2)}"


def generate_demographics() -> dict[str, str | None]:
    """
    Generate realistic demographic data with weighted distributions.
    
    Why we do this:
    - Enables fairness analysis across demographics
    - Uses realistic age/gender/ethnicity distributions
    - Respects privacy by making fields nullable (some users opt out)
    
    Returns:
        Dict with age_range, gender, ethnicity (some may be None)
    """
    # Age distribution (weighted to match general population)
    age_ranges = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_weights = [15, 30, 25, 20, 7, 3]  # Percentages
    age_range = random.choices(age_ranges, weights=age_weights, k=1)[0]
    
    # Gender (some users don't provide - 30% null for privacy)
    genders = ["Male", "Female", "Non-binary", "Prefer not to say", None]
    gender_weights = [35, 35, 5, 5, 30]  # 30% don't provide
    gender = random.choices(genders, weights=gender_weights, k=1)[0]
    
    # Ethnicity (40% don't provide for privacy)
    ethnicities = [
        "White", "Hispanic or Latino", "Black or African American",
        "Asian", "Two or More Races", "Other", None
    ]
    ethnicity_weights = [30, 10, 8, 8, 4, 3, 40]  # 40% don't provide
    ethnicity = random.choices(ethnicities, weights=ethnicity_weights, k=1)[0]
    
    return {
        "age_range": age_range,
        "gender": gender,
        "ethnicity": ethnicity
    }


def generate_users(n: int = 50) -> list[User]:
    """
    Generate synthetic users with demographics and auth credentials.
    
    Why 50 users:
    - Per plan requirements
    - Enough to test all personas
    - Small enough for quick local development
    
    New features:
    - Passwords for authentication (pattern: user{id}123)
    - Demographic data for fairness analysis
    - All users are card_user role by default
    
    Args:
        n: Number of users to generate (default 50)
    
    Returns:
        List of User ORM objects
    """
    logger.info("generating_users", count=n)
    users = []

    for i in range(1, n + 1):
        user_id = generate_user_id(i)
        
        # Generate demographics (weighted distributions)
        demographics = generate_demographics()
        
        # Generate password for authentication
        # Pattern: user001123, user002123, etc. (easy to remember for testing)
        password = f"{user_id.replace('_', '')}123"  # usr_000001 -> usr000001123
        password_hash = hash_password(password)

        # Create via Pydantic for validation
        user_data = UserCreate(
            user_id=user_id,
            # Use friendly labels for the first handful of users so they are easy to pick
            email_masked=(
                FRIENDLY_USER_LABELS[i - 1] if i <= len(FRIENDLY_USER_LABELS) else f"u***{i}@example.com"
            ),
            phone_masked=f"***-***-{str(i).zfill(4)}",
            password=password,  # Will be hashed in model creation
            role="card_user",
            is_active=True,
            age_range=demographics["age_range"],
            gender=demographics["gender"],
            ethnicity=demographics["ethnicity"],
            created_at=datetime.utcnow() - timedelta(days=random.randint(180, 730))
        )

        # Convert to ORM model
        # Override password with already-hashed version
        user_dict = user_data.model_dump()
        user_dict['password_hash'] = password_hash
        del user_dict['password']  # Remove plain password field
        
        user = User(**user_dict)
        users.append(user)

    logger.info("users_generated", count=len(users), demographics_included=True)
    return users


def generate_accounts(session: Session, user: User, user_index: int) -> list[Account]:
    """
    Generate 2-4 accounts per user (checking, savings, credit).
    
    Why this mix:
    - Most people have checking + savings
    - Many have credit cards
    - Variety enables different personas
    
    Args:
        session: Database session
        user: User to create accounts for
        user_index: User's index for ID generation
    
    Returns:
        List of Account ORM objects
    """
    accounts = []
    num_accounts = random.randint(2, 4)

    # Always create checking account (primary)
    checking = AccountCreate(
        account_id=generate_account_id(user_index, 1),
        user_id=user.user_id,
        account_name="Primary Checking",
        account_type="depository",
        account_subtype="checking",
        holder_category="individual",
        currency="USD",
        balance_current=Decimal(str(random.randint(500, 15000))),
        balance_available=None
    )
    accounts.append(Account(**checking.model_dump()))

    # Maybe add savings
    if num_accounts >= 2:
        savings = AccountCreate(
            account_id=generate_account_id(user_index, 2),
            user_id=user.user_id,
            account_name="Savings Account",
            account_type="depository",
            account_subtype="savings",
            holder_category="individual",
            currency="USD",
            balance_current=Decimal(str(random.randint(1000, 50000))),
            balance_available=None
        )
        accounts.append(Account(**savings.model_dump()))

    # Maybe add credit card(s)
    if num_accounts >= 3:
        credit_limit = Decimal(str(random.choice([2000, 5000, 10000, 15000, 25000])))
        # Vary utilization (some high, some low) to create different personas
        utilization_pct = random.choice([10, 25, 35, 55, 70, 85])
        balance = credit_limit * Decimal(utilization_pct) / Decimal(100)

        credit = AccountCreate(
            account_id=generate_account_id(user_index, 3),
            user_id=user.user_id,
            account_name=random.choice(["Chase Sapphire", "Amex Blue", "Discover It", "Capital One Venture"]),
            account_type="credit",
            account_subtype="credit card",
            holder_category="individual",
            currency="USD",
            balance_current=-balance,  # Credit balance is negative
            balance_available=credit_limit - balance,
            credit_limit=credit_limit
        )
        accounts.append(Account(**credit.model_dump()))

    if num_accounts >= 4:
        # Second credit card
        credit_limit = Decimal(str(random.choice([1500, 3000, 5000, 8000])))
        utilization_pct = random.choice([5, 15, 40, 60, 75])
        balance = credit_limit * Decimal(utilization_pct) / Decimal(100)

        credit2 = AccountCreate(
            account_id=generate_account_id(user_index, 4),
            user_id=user.user_id,
            account_name=random.choice(["Visa Rewards", "Mastercard Cash Back", "Target RedCard"]),
            account_type="credit",
            account_subtype="credit card",
            holder_category="individual",
            currency="USD",
            balance_current=-balance,
            balance_available=credit_limit - balance,
            credit_limit=credit_limit
        )
        accounts.append(Account(**credit2.model_dump()))

    return accounts


def generate_transactions(
    session: Session,
    account: Account,
    user_index: int,
    account_index: int,
    days: int = 180
) -> list[Transaction]:
    """
    Generate realistic transactions for an account over N days.
    
    Why these patterns:
    - Subscriptions: monthly recurring (persona trigger)
    - Payroll: bi-weekly or monthly income (persona trigger)
    - Credit payments: monthly (utilization persona)
    - Groceries/dining: variable frequency (realistic spending)
    - Refunds/reversals: edge cases
    
    Args:
        session: Database session
        account: Account to generate transactions for
        user_index: User's index
        account_index: Account's index
        days: How many days back to generate (default 180)
    
    Returns:
        List of Transaction ORM objects
    """
    transactions = []
    tx_counter = 0
    today = date.today()

    # Determine transaction patterns based on account type
    if account.account_subtype == "checking":
        # Generate payroll deposits (income stability signals)
        pay_frequency = random.choice(["biweekly", "monthly"])
        base_salary = random.randint(3000, 8000)

        if pay_frequency == "biweekly":
            # 26 pay periods per year
            for i in range(days // 14):
                tx_date = today - timedelta(days=i * 14)
                # Add some variability for gig workers
                amount = -Decimal(str(base_salary + random.randint(-200, 200)))

                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,  # Negative = credit/income
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name="Payroll ACH",
                    category="Income",
                    subcategory="Paycheck",
                    transaction_type="credit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1
        else:
            # Monthly payroll
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30)
                amount = -Decimal(str(base_salary * 2 + random.randint(-400, 400)))

                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name="Payroll ACH",
                    category="Income",
                    subcategory="Paycheck",
                    transaction_type="credit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1

        # Generate subscription payments (subscription persona trigger)
        num_subscriptions = random.randint(0, 6)
        subscriptions = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(SUBSCRIPTION_MERCHANTS)))

        for merchant in subscriptions:
            # Monthly recurring charge (day of month varies)
            day_of_month = random.randint(1, 28)
            amount_per_month = Decimal(str(random.choice([9.99, 12.99, 14.99, 19.99, 29.99, 49.99])))

            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + day_of_month)
                if tx_date <= today:
                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount_per_month,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name=merchant,
                        category="Subscription",
                        subcategory="Entertainment" if merchant in ["Netflix", "Spotify", "Hulu"] else "Software",
                        transaction_type="debit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Generate utility bills (monthly recurring, different from subscriptions)
        utilities = random.sample(UTILITY_MERCHANTS, random.randint(2, 4))
        for merchant in utilities:
            amount_base = Decimal(str(random.choice([45, 65, 85, 120, 150])))
            day_of_month = random.randint(1, 28)

            for i in range(days // 30):
                # Utilities vary slightly month-to-month
                amount = amount_base + Decimal(str(random.randint(-15, 15)))
                tx_date = today - timedelta(days=i * 30 + day_of_month)
                if tx_date <= today:
                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name=merchant,
                        category="Utilities",
                        subcategory="Bills",
                        transaction_type="debit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Generate groceries (weekly-ish, variable)
        for week in range(days // 7):
            # 1-2 grocery trips per week
            for _ in range(random.randint(1, 2)):
                tx_date = today - timedelta(days=week * 7 + random.randint(0, 6))
                if tx_date <= today:
                    merchant = random.choice(GROCERY_MERCHANTS)
                    amount = Decimal(str(random.randint(40, 200)))

                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name=merchant,
                        category="Food and Drink",
                        subcategory="Groceries",
                        transaction_type="debit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Generate dining (few times per week)
        for week in range(days // 7):
            for _ in range(random.randint(2, 5)):
                tx_date = today - timedelta(days=week * 7 + random.randint(0, 6))
                if tx_date <= today:
                    merchant = random.choice(DINING_MERCHANTS)
                    amount = Decimal(str(random.randint(8, 75)))

                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name=merchant,
                        category="Food and Drink",
                        subcategory="Restaurants",
                        transaction_type="debit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Generate savings transfers (savings builder persona)
        if random.random() > 0.5:  # 50% of users save regularly
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + 15)
                if tx_date <= today:
                    amount = Decimal(str(random.choice([100, 250, 500, 750, 1000])))

                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name="Transfer to Savings",
                        category="Transfer",
                        subcategory="Savings Transfer",
                        transaction_type="transfer"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Add some refunds (edge case: negative amounts for debits)
        for _ in range(random.randint(1, 3)):
            tx_date = today - timedelta(days=random.randint(0, days))
            merchant = random.choice(SHOPPING_MERCHANTS)
            amount = -Decimal(str(random.randint(20, 150)))  # Negative refund

            tx = TransactionCreate(
                transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                account_id=account.account_id,
                amount=amount,
                currency="USD",
                transaction_date=tx_date,
                merchant_name=f"{merchant} Refund",
                category="Shopping",
                subcategory="Refund",
                transaction_type="credit"
            )
            transactions.append(Transaction(**tx.model_dump()))
            tx_counter += 1

    elif account.account_subtype == "savings":
        # Savings accounts have fewer transactions
        # Mainly transfers from checking
        for i in range(days // 30):
            if random.random() > 0.3:  # Not every month
                tx_date = today - timedelta(days=i * 30 + 15)
                if tx_date <= today:
                    amount = -Decimal(str(random.choice([100, 250, 500, 750, 1000])))  # Incoming transfer

                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name="Transfer from Checking",
                        category="Transfer",
                        subcategory="Savings Transfer",
                        transaction_type="credit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

        # Occasional interest payments
        for i in range(days // 90):
            tx_date = today - timedelta(days=i * 90)
            if tx_date <= today:
                amount = -Decimal(str(random.randint(1, 20)))  # Small interest

                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name="Interest Earned",
                    category="Income",
                    subcategory="Interest",
                    transaction_type="credit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1

    elif account.account_subtype == "credit card":
        # Credit card payments (monthly)
        for i in range(days // 30):
            tx_date = today - timedelta(days=i * 30 + 5)
            if tx_date <= today:
                # Payment amount (sometimes minimum, sometimes more)
                if random.random() > 0.7:
                    # Minimum payment only (high utilization persona trigger)
                    amount = -Decimal(str(random.randint(25, 50)))
                else:
                    # Larger payment
                    amount = -Decimal(str(random.randint(100, 1500)))

                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name="Payment - Thank You",
                    category="Payment",
                    subcategory="Credit Card Payment",
                    transaction_type="credit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1

        # Credit card purchases (variable)
        for _ in range(random.randint(20, 60)):
            tx_date = today - timedelta(days=random.randint(0, days))
            if tx_date <= today:
                merchant = random.choice(SHOPPING_MERCHANTS + DINING_MERCHANTS + GROCERY_MERCHANTS)
                amount = Decimal(str(random.randint(15, 300)))

                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name=merchant,
                    category="Shopping",
                    subcategory="General",
                    transaction_type="debit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1

        # Interest charges (high utilization persona trigger)
        if random.random() > 0.6:  # 40% of credit accounts have interest
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + 25)
                if tx_date <= today:
                    amount = Decimal(str(random.randint(15, 120)))

                    tx = TransactionCreate(
                        transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                        account_id=account.account_id,
                        amount=amount,
                        currency="USD",
                        transaction_date=tx_date,
                        merchant_name="Interest Charge",
                        category="Fees",
                        subcategory="Interest Charged",
                        transaction_type="debit"
                    )
                    transactions.append(Transaction(**tx.model_dump()))
                    tx_counter += 1

    return transactions


def generate_liabilities(session: Session, user: User, user_index: int, accounts: list[Account]) -> list[Liability]:
    """
    Generate liabilities (credit cards, loans) for a user.
    
    Why this matters:
    - Credit utilization drives High Utilization persona
    - Minimum payments and overdue flags are key signals
    - Interest rates inform recommendations
    
    Args:
        session: Database session
        user: User to create liabilities for
        user_index: User's index
        accounts: User's accounts (to link credit cards)
    
    Returns:
        List of Liability ORM objects
    """
    liabilities = []
    liability_counter = 0

    # Create liabilities for credit card accounts
    credit_accounts = [acc for acc in accounts if acc.account_subtype == "credit card"]

    for acc in credit_accounts:
        # Credit limit from account
        credit_limit = acc.credit_limit if acc.credit_limit else Decimal("5000")
        # Current balance (negative in account, positive in liability)
        current_balance = -acc.balance_current if acc.balance_current < 0 else Decimal("0")

        # Calculate minimum payment (typically 2-3% of balance or $25, whichever is higher)
        # Round to 2 decimal places to match Pydantic validation
        min_payment = max(current_balance * Decimal("0.025"), Decimal("25")).quantize(Decimal("0.01"))

        # Interest rate (varies by creditworthiness)
        interest_rate = Decimal(str(random.choice([15.99, 18.99, 21.99, 24.99])))

        # Sometimes overdue (persona trigger)
        is_overdue = random.random() > 0.85  # 15% overdue

        liab = LiabilityCreate(
            liability_id=generate_liability_id(user_index, liability_counter),
            user_id=user.user_id,
            account_id=acc.account_id,
            liability_type="credit_card",
            name=acc.account_name,
            current_balance=current_balance,
            credit_limit=credit_limit,
            minimum_payment=min_payment,
            last_payment_amount=Decimal(str(random.randint(50, 500))) if random.random() > 0.3 else None,
            last_payment_date=date.today() - timedelta(days=random.randint(5, 35)) if random.random() > 0.2 else None,
            next_payment_due_date=date.today() + timedelta(days=random.randint(5, 30)),
            interest_rate_percentage=interest_rate,
            is_overdue=is_overdue
        )
        liabilities.append(Liability(**liab.model_dump()))
        liability_counter += 1

    # Maybe add a student loan
    if random.random() > 0.6:  # 40% have student loans
        loan_balance = Decimal(str(random.randint(10000, 80000)))
        min_payment = Decimal(str(random.randint(150, 600)))

        liab = LiabilityCreate(
            liability_id=generate_liability_id(user_index, liability_counter),
            user_id=user.user_id,
            account_id=None,
            liability_type="student_loan",
            name="Federal Student Loan",
            current_balance=loan_balance,
            credit_limit=None,  # Loans don't have credit limits
            minimum_payment=min_payment,
            last_payment_amount=min_payment if random.random() > 0.2 else None,
            last_payment_date=date.today() - timedelta(days=random.randint(10, 40)) if random.random() > 0.3 else None,
            next_payment_due_date=date.today() + timedelta(days=random.randint(10, 30)),
            interest_rate_percentage=Decimal(str(random.choice([4.99, 5.99, 6.99]))),
            is_overdue=random.random() > 0.9  # 10% overdue
        )
        liabilities.append(Liability(**liab.model_dump()))
        liability_counter += 1

    return liabilities


def seed_database() -> None:
    """
    Main function to seed the database with synthetic data.
    
    Why this orchestrates everything:
    - Generates all entities in correct order (users → accounts → transactions → liabilities)
    - Uses single transaction for atomicity
    - Provides clear logging for debugging
    - Deterministic due to SEED configuration
    
    Generates:
    - 50 users
    - 2-4 accounts per user
    - 180 days of transactions per account
    - 1-3 liabilities per user
    - Consent events for all users
    
    Usage:
        from spendsense.app.db.session import init_db
        from spendsense.app.db.seed import seed_database
        
        init_db()
        seed_database()
    """
    logger.info("starting_database_seed", seed=settings.seed)

    with next(get_session()) as session:
        # Generate users
        users = generate_users(n=50)
        session.add_all(users)
        session.flush()  # Get user IDs without committing

        logger.info("users_added_to_session", count=len(users))

        all_accounts = []
        all_transactions = []
        all_liabilities = []
        all_consents = []

        # Generate accounts, transactions, liabilities for each user
        for idx, user in enumerate(users, start=1):
            # Accounts
            accounts = generate_accounts(session, user, idx)
            all_accounts.extend(accounts)
            session.add_all(accounts)
            session.flush()

            # Transactions for each account
            for acc_idx, account in enumerate(accounts, start=1):
                transactions = generate_transactions(session, account, idx, acc_idx, days=180)
                all_transactions.extend(transactions)

            # Liabilities
            liabilities = generate_liabilities(session, user, idx, accounts)
            all_liabilities.extend(liabilities)

            # Consent (most users opt in)
            if random.random() > 0.1:  # 90% opt in
                consent = ConsentEventCreate(
                    user_id=user.user_id,
                    action="opt_in",
                    reason="Initial signup",
                    consent_given_by="user_dashboard",
                    timestamp=user.created_at + timedelta(minutes=5)
                )
                all_consents.append(ConsentEvent(**consent.model_dump()))
            else:
                # 10% opt out or haven't decided yet
                if random.random() > 0.5:
                    consent = ConsentEventCreate(
                        user_id=user.user_id,
                        action="opt_out",
                        reason="Privacy concerns",
                        consent_given_by="user_dashboard",
                        timestamp=user.created_at + timedelta(days=random.randint(1, 30))
                    )
                    all_consents.append(ConsentEvent(**consent.model_dump()))

        # Add all to session
        session.add_all(all_transactions)
        session.add_all(all_liabilities)
        session.add_all(all_consents)

        # Commit everything
        session.commit()

        logger.info(
            "database_seeded_successfully",
            users=len(users),
            accounts=len(all_accounts),
            transactions=len(all_transactions),
            liabilities=len(all_liabilities),
            consents=len(all_consents)
        )


def ingest_from_csv(file_path: str) -> dict[str, Any]:
    """
    Ingest data from CSV file with validation.
    
    Why CSV support:
    - Simple format for data import
    - Easy to create sample files
    - Common in financial data exports
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        Dict with success/error counts and messages
    
    Example CSV format for users:
        user_id,email_masked,phone_masked
        usr_001,u***1@example.com,***-***-0001
        usr_002,u***2@example.com,***-***-0002
    """
    logger.info("ingesting_from_csv", file_path=file_path)

    results: dict[str, Any] = {
        "success_count": 0,
        "error_count": 0,
        "errors": []
    }

    try:
        with open(file_path) as csvfile:
            reader = csv.DictReader(csvfile)

            with next(get_session()) as session:
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # Attempt to validate and create user (assuming users CSV for now)
                        user_data = UserCreate(**row)  # type: ignore[arg-type]
                        user = User(**user_data.model_dump())
                        session.add(user)
                        results["success_count"] += 1
                    except ValidationError as e:
                        error_msg = f"Row {row_num}: {str(e)}"
                        results["errors"].append(error_msg)  # type: ignore
                        results["error_count"] += 1
                        logger.warning("csv_validation_error", row=row_num, error=str(e))
                    except Exception as e:
                        error_msg = f"Row {row_num}: Unexpected error - {str(e)}"
                        results["errors"].append(error_msg)  # type: ignore
                        results["error_count"] += 1
                        logger.error("csv_ingestion_error", row=row_num, error=str(e))

                # Commit valid records even if some failed
                session.commit()

        logger.info(
            "csv_ingestion_complete",
            file=file_path,
            success=results["success_count"],
            errors=results["error_count"]
        )
    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        results["errors"].append(error_msg)  # type: ignore
        logger.error("csv_file_not_found", file_path=file_path)

    return results


def ingest_from_json(file_path: str) -> dict[str, Any]:
    """
    Ingest data from JSON file with validation.
    
    Why JSON support:
    - Flexible structure (nested objects)
    - Common API format
    - Easy to represent complex data
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Dict with success/error counts and messages
    
    Example JSON format for transactions:
        [
            {
                "transaction_id": "txn_001",
                "account_id": "acc_001",
                "amount": "45.99",
                "currency": "USD",
                "transaction_date": "2024-01-15",
                "merchant_name": "Starbucks"
            }
        ]
    """
    logger.info("ingesting_from_json", file_path=file_path)

    results: dict[str, Any] = {
        "success_count": 0,
        "error_count": 0,
        "errors": []
    }

    try:
        with open(file_path) as jsonfile:
            data = json.load(jsonfile)

            if not isinstance(data, list):
                data = [data]

            with next(get_session()) as session:
                for idx, record in enumerate(data, start=1):
                    try:
                        # Attempt to validate and create transaction (assuming transactions JSON for now)
                        tx_data = TransactionCreate(**record)
                        tx = Transaction(**tx_data.model_dump())
                        session.add(tx)
                        results["success_count"] += 1
                    except ValidationError as e:
                        error_msg = f"Record {idx}: {str(e)}"
                        results["errors"].append(error_msg)  # type: ignore
                        results["error_count"] += 1
                        logger.warning("json_validation_error", record=idx, error=str(e))
                    except Exception as e:
                        error_msg = f"Record {idx}: Unexpected error - {str(e)}"
                        results["errors"].append(error_msg)  # type: ignore
                        results["error_count"] += 1
                        logger.error("json_ingestion_error", record=idx, error=str(e))

                # Commit valid records even if some failed
                session.commit()

        logger.info(
            "json_ingestion_complete",
            file=file_path,
            success=results["success_count"],
            errors=results["error_count"]
        )
    except FileNotFoundError:
        error_msg = f"File not found: {file_path}"
        results["errors"].append(error_msg)  # type: ignore
        logger.error("json_file_not_found", file_path=file_path)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {str(e)}"
        results["errors"].append(error_msg)  # type: ignore
        logger.error("json_decode_error", error=str(e))

    return results

