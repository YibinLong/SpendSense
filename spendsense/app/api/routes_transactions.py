"""
Transaction API routes.

This module provides endpoints for retrieving user transactions.

Endpoints:
- GET /transactions/{user_id} - Get transactions for a user

Why this exists:
- Users need to view their transaction history
- Supports filtering and pagination
- NO consent required - transactions are raw data always accessible to users
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Account, Transaction, User
from spendsense.app.db.session import get_db
from spendsense.app.schemas.transaction import Transaction as TransactionSchema

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{user_id}")
async def get_user_transactions(
    user_id: str,
    limit: int | None = Query(default=100, description="Number of transactions to return", le=1000),
    offset: int | None = Query(default=0, description="Number of transactions to skip"),
    db: Session = Depends(get_db),
) -> list[TransactionSchema]:
    """
    Get transactions for a user.
    
    **NO CONSENT REQUIRED** - Transactions are raw financial data that users
    always have the right to view. Consent is only required for PROCESSING
    data into behavioral insights, personas, and recommendations.
    
    Per PRD: "Require explicit opt-in before processing data" means processing
    into behavioral signals, NOT viewing raw transaction history.
    
    Why this exists:
    - Users need to see their transaction history
    - Transactions are sorted by date (newest first)
    - Supports pagination with limit and offset
    - No consent check - raw data is always accessible
    
    Query params:
        limit: Number of transactions to return (default 100, max 1000)
        offset: Number of transactions to skip (default 0)
    
    Response:
        List of transactions sorted by transaction_date descending
    
    Returns 404 if user not found.
    """
    logger.info("getting_transactions", user_id=user_id, limit=limit, offset=offset)

    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    # Get user's accounts
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    account_ids = [acc.account_id for acc in accounts]

    # Get transactions for user's accounts, sorted by date (newest first)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id.in_(account_ids))
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    logger.info("transactions_retrieved", user_id=user_id, count=len(transactions))

    # Convert to schema
    return [TransactionSchema.model_validate(tx) for tx in transactions]

