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


# Persona-specific user data for easy debugging and clean UX
# 10 users per persona (50 total users)
# Format: (first_name, last_name, description)
PERSONA_USERS = {
    "high_utilization": [
        ("Alice", "Martinez", "Heavy credit card user"),
        ("Bob", "Thompson", "Maxed out cards"),
        ("Carol", "Rodriguez", "Paying interest charges"),
        ("Dave", "Anderson", "High credit balances"),
        ("Eve", "Williams", "Near credit limit"),
        ("Marcus", "Bennett", "Struggling with debt"),
        ("Nina", "Foster", "Multiple maxed cards"),
        ("Oscar", "Hughes", "High interest payments"),
        ("Priya", "Shah", "Credit repair needed"),
        ("Ryan", "Sullivan", "Over credit limit"),
    ],
    "savings_builder": [
        ("Frank", "Garcia", "Consistent saver"),
        ("Grace", "Chen", "Growing emergency fund"),
        ("Henry", "Patel", "Auto-save enthusiast"),
        ("Iris", "Johnson", "High savings rate"),
        ("Jack", "Kim", "Building wealth"),
        ("Maya", "Brooks", "Smart saver"),
        ("Nathan", "Reed", "Emergency fund pro"),
        ("Sophia", "Nguyen", "Automated savings"),
        ("Tyler", "Coleman", "Long-term planner"),
        ("Zoe", "Mitchell", "Financial goals achiever"),
    ],
    "subscription_heavy": [
        ("Kelly", "Brown", "Many subscriptions"),
        ("Liam", "Davis", "Streaming services fan"),
        ("Mia", "Wilson", "Service collector"),
        ("Noah", "Taylor", "Monthly recurring bills"),
        ("Olivia", "Moore", "Subscription overload"),
        ("Aiden", "Cooper", "Digital service addict"),
        ("Bella", "Rivera", "Streaming everything"),
        ("Caleb", "Barnes", "Too many memberships"),
        ("Diana", "Powell", "Subscription reviewer"),
        ("Ethan", "Russell", "Recurring payment king"),
    ],
    "variable_income_budgeter": [
        ("Paul", "Jackson", "Freelance designer"),
        ("Quinn", "White", "Gig economy worker"),
        ("Rita", "Harris", "Irregular paychecks"),
        ("Sam", "Martin", "Self-employed consultant"),
        ("Tara", "Lopez", "Contract worker"),
        ("Isaac", "Murphy", "Freelance writer"),
        ("Julia", "Price", "Independent contractor"),
        ("Kevin", "Bell", "Side hustle expert"),
        ("Laura", "Sanders", "Consulting business owner"),
        ("Miles", "Perry", "Variable income pro"),
    ],
    "cash_flow_optimizer": [
        ("Uma", "Lee", "Tight monthly budget"),
        ("Victor", "Clark", "Low cash buffer"),
        ("Wendy", "Lewis", "Paycheck to paycheck"),
        ("Xavier", "Walker", "Budget conscious"),
        ("Yara", "Hall", "Expense optimizer"),
        ("Blake", "Ross", "Living close to budget"),
        ("Chloe", "Henderson", "Cash flow manager"),
        ("Derek", "Griffin", "Monthly balancer"),
        ("Emma", "Patterson", "Budget stretcher"),
        ("Felix", "Jenkins", "Smart spender"),
    ],
}


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


def generate_demographics() -> dict[str, str]:
    """
    Generate realistic demographic data with weighted distributions.
    
    Why we do this:
    - Enables fairness analysis across demographics
    - Uses realistic age/gender/ethnicity distributions
    - All users have complete demographic data for better fairness analysis
    
    Returns:
        Dict with age_range, gender, ethnicity (all values populated)
    """
    # Age distribution (weighted to match general population)
    age_ranges = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_weights = [15, 30, 25, 20, 7, 3]  # Percentages
    age_range = random.choices(age_ranges, weights=age_weights, k=1)[0]
    
    # Gender distribution (everyone provides data for fairness analysis)
    genders = ["Male", "Female", "Non-binary", "Prefer not to say"]
    gender_weights = [45, 45, 5, 5]  # Balanced distribution
    gender = random.choices(genders, weights=gender_weights, k=1)[0]
    
    # Ethnicity (everyone provides data for comprehensive fairness analysis)
    ethnicities = [
        "White", "Hispanic or Latino", "Black or African American",
        "Asian", "Two or More Races", "Other"
    ]
    ethnicity_weights = [50, 15, 13, 13, 6, 3]  # Realistic US distribution
    ethnicity = random.choices(ethnicities, weights=ethnicity_weights, k=1)[0]
    
    return {
        "age_range": age_range,
        "gender": gender,
        "ethnicity": ethnicity
    }


def generate_users(n: int = 50) -> list[User]:
    """
    Generate synthetic users with predetermined personas for easy testing.
    
    NEW DESIGN:
    - 50 total users (10 per persona)
    - Real names and clean emails (firstname.lastname@example.com)
    - Simple passwords (firstname123)
    - Deterministic generation based on seed
    - Easy to debug: name tells you expected persona
    
    Personas generated:
    - 10x high_utilization users
    - 10x savings_builder users
    - 10x subscription_heavy users
    - 10x variable_income_budgeter users
    - 10x cash_flow_optimizer users
    
    Args:
        n: Number of users to generate (default 50, must be multiple of 5)
    
    Returns:
        List of User ORM objects
    """
    logger.info("generating_users", count=n)
    
    # Personas in order
    personas = ["high_utilization", "savings_builder", "subscription_heavy", 
                "variable_income_budgeter", "cash_flow_optimizer"]
    
    users = []
    user_counter = 1

    for persona in personas:
        persona_user_data = PERSONA_USERS[persona]
        for first_name, last_name, description in persona_user_data:
            # Generate clean IDs and emails
            user_id = f"{first_name.lower()}.{last_name.lower()}"
            # Store name in email_masked as "First Last <email@example.com>"
            # This allows frontend to parse and display nicely
            email = f"{first_name} {last_name} <{first_name.lower()}.{last_name.lower()}@example.com>"
            
            # Generate demographics (weighted distributions)
            demographics = generate_demographics()
            
            # Simple password: firstname123 (e.g., alice123, bob123)
            password = f"{first_name.lower()}123"
            password_hash = hash_password(password)

            # Create via Pydantic for validation
            user_data = UserCreate(
                user_id=user_id,
                email_masked=email,
                phone_masked=f"***-***-{str(user_counter).zfill(4)}",
                password=password,
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
            # Store expected persona and display name as temporary attributes
            user._expected_persona = persona  # type: ignore
            user._display_name = f"{first_name} {last_name}"  # type: ignore
            user._description = description  # type: ignore
            users.append(user)
            
            user_counter += 1

    logger.info("users_generated", count=len(users), personas=len(personas), demographics_included=True)
    return users


def generate_accounts(session: Session, user: User, user_index: int, expected_persona: str | None = None) -> list[Account]:
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
        # PERSONA-SPECIFIC utilization
        if expected_persona == "high_utilization":
            utilization_pct = random.choice([55, 65, 75, 85, 95])  # High utilization ≥50%
        elif expected_persona == "savings_builder":
            utilization_pct = random.choice([5, 10, 15, 20, 25])  # Low utilization <30%
        elif expected_persona in ["subscription_heavy", "cash_flow_optimizer", "variable_income_budgeter"]:
            utilization_pct = random.choice([15, 25, 35, 40])  # Moderate <50%
        else:
            utilization_pct = random.choice([10, 25, 35, 55, 70, 85])  # Default random
        
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
        # PERSONA-SPECIFIC utilization (same as first card)
        if expected_persona == "high_utilization":
            utilization_pct = random.choice([55, 65, 75, 85])
        elif expected_persona == "savings_builder":
            utilization_pct = random.choice([5, 10, 15, 20])
        elif expected_persona in ["subscription_heavy", "cash_flow_optimizer", "variable_income_budgeter"]:
            utilization_pct = random.choice([15, 25, 30, 40])
        else:
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
    days: int = 180,
    expected_persona: str | None = None
) -> list[Transaction]:
    """
    Generate realistic transactions for an account over N days.
    
    Why these patterns:
    - Subscriptions: monthly recurring (persona trigger)
    - Payroll: bi-weekly or monthly income (persona trigger)
    - Credit payments: monthly (utilization persona)
    - Groceries/dining: variable frequency (realistic spending)
    - Refunds/reversals: edge cases
    
    PERSONA-SPECIFIC GENERATION:
    - Uses expected_persona to generate transactions that will trigger correct persona assignment
    - Ensures users get assigned to their intended personas
    
    Args:
        session: Database session
        account: Account to generate transactions for
        user_index: User's index
        account_index: Account's index
        days: How many days back to generate (default 180)
        expected_persona: Expected persona for this user (for tailored transaction generation)
    
    Returns:
        List of Transaction ORM objects
    """
    transactions = []
    tx_counter = 0
    today = date.today()

    # Determine transaction patterns based on account type
    if account.account_subtype == "checking":
        # Generate payroll deposits (income stability signals)
        # PERSONA-SPECIFIC: Variable income budgeters need irregular pay gaps
        if expected_persona == "variable_income_budgeter":
            # Irregular income: 60-90 day gaps between paychecks
            # This will trigger: median_pay_gap > 45 days
            # PLUS low income to ensure cashflow_buffer < 1 month
            pay_dates = []
            current_date = today
            while current_date > today - timedelta(days=days):
                pay_dates.append(current_date)
                # Irregular gaps: 60-90 days (MUST be > 45 for persona)
                gap_days = random.randint(60, 90)
                current_date = current_date - timedelta(days=gap_days)
            
            # REDUCED base salary to ensure low cashflow buffer
            base_salary = random.randint(1500, 2500)  # Lower income for buffer < 1 month
            for tx_date in pay_dates:
                # High variability in amount (freelance/gig work)
                amount = -Decimal(str(base_salary + random.randint(-500, 500)))
                if amount > 0:  # Ensure it's income (negative = credit)
                    amount = -abs(amount)
                
                tx = TransactionCreate(
                    transaction_id=generate_transaction_id(user_index, account_index, tx_counter),
                    account_id=account.account_id,
                    amount=amount,
                    currency="USD",
                    transaction_date=tx_date,
                    merchant_name="Freelance Payment",
                    category="Income",
                    subcategory="Paycheck",  # MUST be "Paycheck" for payroll detection!
                    transaction_type="credit"
                )
                transactions.append(Transaction(**tx.model_dump()))
                tx_counter += 1
        else:
            # Regular income for other personas
            pay_frequency = random.choice(["biweekly", "monthly"])
            base_salary = random.randint(3000, 8000)

            if pay_frequency == "biweekly":
                # 26 pay periods per year
                for i in range(days // 14):
                    tx_date = today - timedelta(days=i * 14)
                    # Small variability for regular workers
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
        # PERSONA-SPECIFIC: Subscription-heavy users need ≥3 merchants AND ≥$50/month
        if expected_persona == "subscription_heavy":
            num_subscriptions = random.randint(3, 6)  # Ensure ≥3 for persona match
        elif expected_persona == "high_utilization":
            num_subscriptions = random.randint(1, 2)  # Don't trigger subscription persona
        elif expected_persona == "variable_income_budgeter":
            num_subscriptions = random.randint(0, 1)  # Few subscriptions
        else:
            num_subscriptions = random.randint(0, 2)  # Below threshold
        
        subscriptions = random.sample(SUBSCRIPTION_MERCHANTS, min(num_subscriptions, len(SUBSCRIPTION_MERCHANTS)))

        for merchant in subscriptions:
            # Monthly recurring charge (day of month varies)
            day_of_month = random.randint(1, 28)
            # PERSONA-SPECIFIC: Subscription-heavy users need higher amounts to reach ≥$50 total
            if expected_persona == "subscription_heavy":
                amount_per_month = Decimal(str(random.choice([14.99, 19.99, 29.99, 49.99])))  # Higher amounts
            else:
                amount_per_month = Decimal(str(random.choice([9.99, 12.99, 14.99, 19.99])))  # Lower amounts

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
        # PERSONA-SPECIFIC: Control spending to influence buffer
        if expected_persona == "variable_income_budgeter":
            # AGGRESSIVE spending to create low buffer with irregular income
            # Need buffer < 1 month, so spend heavily
            grocery_frequency = random.randint(3, 4)  # Many trips
            grocery_amount_range = (80, 300)  # HIGH amounts
        elif expected_persona == "cash_flow_optimizer":
            # CALIBRATED spending to hit buffer 0.5-1.0 month range
            grocery_frequency = 2
            grocery_amount_range = (60, 140)  # Moderate-high
        else:
            # Normal spending
            grocery_frequency = random.randint(1, 2)
            grocery_amount_range = (40, 200)
        
        for week in range(days // 7):
            for _ in range(grocery_frequency):
                tx_date = today - timedelta(days=week * 7 + random.randint(0, 6))
                if tx_date <= today:
                    merchant = random.choice(GROCERY_MERCHANTS)
                    amount = Decimal(str(random.randint(grocery_amount_range[0], grocery_amount_range[1])))

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
        # PERSONA-SPECIFIC: Variable income budgeters spend more on dining too
        if expected_persona == "variable_income_budgeter":
            dining_frequency = random.randint(4, 7)  # Lots of dining out
            dining_amount_range = (20, 120)  # Higher amounts
        elif expected_persona == "cash_flow_optimizer":
            # Moderate dining to hit 0.5-1.0 month buffer sweet spot
            dining_frequency = random.randint(3, 5)
            dining_amount_range = (15, 85)
        else:
            dining_frequency = random.randint(2, 5)
            dining_amount_range = (8, 75)
        
        for week in range(days // 7):
            for _ in range(dining_frequency):
                tx_date = today - timedelta(days=week * 7 + random.randint(0, 6))
                if tx_date <= today:
                    merchant = random.choice(DINING_MERCHANTS)
                    amount = Decimal(str(random.randint(dining_amount_range[0], dining_amount_range[1])))

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
        # PERSONA-SPECIFIC: Control savings to match persona criteria
        if expected_persona == "savings_builder":
            # Force regular savings: $200-1000/month to ensure net inflow ≥$200
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + 15)
                if tx_date <= today:
                    amount = Decimal(str(random.choice([250, 500, 750, 1000])))  # Higher amounts

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
        elif expected_persona == "cash_flow_optimizer":
            # VERY SMALL/irregular savings to hit 0.5-1.0 month buffer sweet spot
            for i in range(days // 90):  # Every 3 months
                if random.random() > 0.5:  # Skip half the time
                    tx_date = today - timedelta(days=i * 90 + 15)
                    if tx_date <= today:
                        amount = Decimal(str(random.choice([30, 50, 75, 100])))  # Small amounts

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
        elif expected_persona == "variable_income_budgeter":
            # No regular savings - low buffer is key criteria
            pass  # Skip savings transfers
        elif expected_persona == "subscription_heavy":
            # Some savings but not primary focus
            if random.random() > 0.5:
                for i in range(days // 60):
                    tx_date = today - timedelta(days=i * 60 + 15)
                    if tx_date <= today:
                        amount = Decimal(str(random.choice([100, 200, 300])))

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
        # else: high_utilization and others get no savings transfers (default)

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
        # PERSONA-SPECIFIC: Match the checking account savings transfers
        if expected_persona == "savings_builder":
            # Regular deposits: $200-1000/month
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + 15)
                if tx_date <= today:
                    amount = -Decimal(str(random.choice([250, 500, 750, 1000])))  # Incoming transfer

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
        elif expected_persona == "cash_flow_optimizer":
            # VERY SMALL/irregular deposits to keep buffer in 0.5-1.0 range
            # Less frequent and smaller amounts
            for i in range(days // 90):  # Every 3 months
                if random.random() > 0.5:  # Skip half the time
                    tx_date = today - timedelta(days=i * 90 + 15)
                    if tx_date <= today:
                        amount = -Decimal(str(random.choice([30, 50, 75, 100])))

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
        elif expected_persona == "subscription_heavy":
            # Some deposits
            for i in range(days // 60):
                if random.random() > 0.5:
                    tx_date = today - timedelta(days=i * 60 + 15)
                    if tx_date <= today:
                        amount = -Decimal(str(random.choice([100, 200, 300])))

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
        # else: variable_income_budgeter and high_utilization get minimal/no deposits

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
        # PERSONA-SPECIFIC: Control payment amounts to influence utilization
        for i in range(days // 30):
            tx_date = today - timedelta(days=i * 30 + 5)
            if tx_date <= today:
                # Payment amount varies by persona
                if expected_persona == "high_utilization":
                    # Minimum payments only to maintain high balances
                    amount = -Decimal(str(random.randint(25, 75)))
                elif expected_persona == "savings_builder":
                    # Pay off in full to keep utilization low
                    amount = -Decimal(str(random.randint(500, 2000)))
                else:
                    # Moderate payments
                    amount = -Decimal(str(random.randint(100, 800)))

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
        # PERSONA-SPECIFIC: Control purchase amounts to create correct utilization levels
        if expected_persona == "high_utilization":
            # More purchases, higher amounts to create ≥50% utilization
            num_purchases = random.randint(40, 70)
            amount_range = (50, 400)  # Higher amounts
        elif expected_persona == "savings_builder":
            # Fewer purchases, lower amounts to keep utilization <30%
            num_purchases = random.randint(10, 25)
            amount_range = (10, 100)  # Lower amounts
        elif expected_persona in ["cash_flow_optimizer", "variable_income_budgeter"]:
            # Moderate purchases for <50% utilization
            num_purchases = random.randint(20, 40)
            amount_range = (15, 200)
        else:
            # Default
            num_purchases = random.randint(20, 60)
            amount_range = (15, 300)
        
        for _ in range(num_purchases):
            tx_date = today - timedelta(days=random.randint(0, days))
            if tx_date <= today:
                merchant = random.choice(SHOPPING_MERCHANTS + DINING_MERCHANTS + GROCERY_MERCHANTS)
                amount = Decimal(str(random.randint(amount_range[0], amount_range[1])))

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
        # PERSONA-SPECIFIC: ONLY high_utilization users get interest charges!
        # This prevents other personas from being incorrectly classified as high_utilization
        if expected_persona == "high_utilization":
            # FORCE interest charges every month (guarantees persona match)
            for i in range(days // 30):
                tx_date = today - timedelta(days=i * 30 + 25)
                if tx_date <= today:
                    amount = Decimal(str(random.randint(30, 150)))  # Higher interest

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
        # ALL other personas: NO interest charges to avoid high_utilization classification

    return transactions


def generate_liabilities(session: Session, user: User, user_index: int, accounts: list[Account], expected_persona: str | None = None) -> list[Liability]:
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

        # Overdue status - PERSONA-SPECIFIC
        # ONLY high_utilization users can be overdue (otherwise triggers wrong persona)
        if expected_persona == "high_utilization":
            is_overdue = random.random() > 0.7  # 30% overdue for high_utilization users
        else:
            is_overdue = False  # Never overdue for other personas

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
    
    NEW: Generates 50 users (10 per persona) for easier testing
    
    Generates:
    - 50 users (10 per persona with descriptive names)
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
        # Create operator account first
        operator_password_hash = hash_password("operator123")
        operator_demographics = generate_demographics()  # Operator needs demographics too for fairness analysis
        operator = User(
            user_id="operator@spendsense.local",
            email_masked="operator@spendsense.local",
            password_hash=operator_password_hash,
            role="operator",
            is_active=True,
            age_range=operator_demographics["age_range"],
            gender=operator_demographics["gender"],
            ethnicity=operator_demographics["ethnicity"],
            created_at=datetime.utcnow()
        )
        session.add(operator)
        session.flush()
        logger.info("operator_account_created", user_id="operator@spendsense.local")
        
        # Generate users (50 users: 10 per persona)
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
            expected_persona = getattr(user, '_expected_persona', None)
            accounts = generate_accounts(session, user, idx, expected_persona=expected_persona)
            all_accounts.extend(accounts)
            session.add_all(accounts)
            session.flush()

            # Transactions for each account
            for acc_idx, account in enumerate(accounts, start=1):
                # Pass expected persona to ensure correct transaction patterns
                expected_persona = getattr(user, '_expected_persona', None)
                transactions = generate_transactions(session, account, idx, acc_idx, days=180, expected_persona=expected_persona)
                all_transactions.extend(transactions)

            # Liabilities
            expected_persona = getattr(user, '_expected_persona', None)
            liabilities = generate_liabilities(session, user, idx, accounts, expected_persona=expected_persona)
            all_liabilities.extend(liabilities)

            # Consent - ALL users start WITHOUT consent (opt_out by default)
            # Why: This ensures users must explicitly grant consent before viewing insights
            # This improves privacy and demonstrates the consent flow correctly
            consent = ConsentEventCreate(
                user_id=user.user_id,
                action="opt_out",
                reason="Default privacy setting - no consent given yet",
                consent_given_by="system",
                timestamp=user.created_at + timedelta(minutes=1)
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

