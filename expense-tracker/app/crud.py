from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import List, Dict
from datetime import datetime, timedelta

async def get_monthly_summary(db: Session, user_id: int) -> List[Dict]:
    # Optimize with single query instead of multiple queries
    result = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= (datetime.utcnow() - timedelta(days=30))
        )
        .group_by(Transaction.category)
        .all()
    )
    return [{"category": r.category, "total": float(r.total), "count": r.count} for r in result]

async def get_user_transactions(db: Session, user_id: int) -> List[Transaction]:
    # Use selectinload for eager loading of relationships
    return (
        db.query(Transaction)
        .options(selectinload(Transaction.owner))
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.date.desc())
        .all()
    )
