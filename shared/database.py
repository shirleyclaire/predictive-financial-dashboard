from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlmodel import SQLModel, Field, create_engine, Session
from datetime import date, datetime
import os
from typing import List
from shared.config import get_settings

class FinancialTransaction(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    amount: float
    category: str
    date: date
    user_id: int
    type: str  # "income" or "expense"

class UpcomingBill(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int
    amount: float
    due_date: date
    description: str

class UserProfile(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    current_balance: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class FinancialInsight(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int
    date_generated: datetime = Field(default_factory=datetime.utcnow)
    insights: List[str] = Field(default=[])
    category_distribution: dict
    month_comparison: dict

class SavingsGoal(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int
    target_amount: float
    current_amount: float = Field(default=0.0)
    start_date: date = Field(default_factory=date.today)
    deadline: date
    category: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    progress_history: List[dict] = Field(default=[])

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

def get_db():
    with Session(engine) as session:
        yield session

async def store_weekly_insights():
    async with AsyncSessionLocal() as session:
        # Weekly trigger logic will be handled by the application
        pass

SQLModel.metadata.create_all(engine)
