from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend
from pydantic import BaseModel
from sqlmodel import Session, select
from shared.database import get_db, FinancialTransaction
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import httpx
import os
from services.auth_service import verify_token
from collections import defaultdict
from shared.sample_data import generate_sample_transactions
from services.openrouter_service import OpenRouterService
from shared.exceptions import (
    DatabaseError, OpenRouterError, ValidationError,
    AuthenticationError, RateLimitError,
    database_exception_handler, http_exception_handler,
    validation_exception_handler
)
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()

# Add exception handlers
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

class Transaction(BaseModel):
    amount: float
    category: str
    date: str
    type: str

class BillRequest(BaseModel):
    amount: float
    due_date: str
    description: str

class CashFlowRequest(BaseModel):
    current_balance: float
    upcoming_bills: List[BillRequest]
    user_id: int

class LoanPredictionRequest(BaseModel):
    credit_score: int
    monthly_income: float
    existing_loans: List[float]
    payment_history_percent: float
    monthly_savings: float

class TransactionCreate(BaseModel):
    amount: float
    category: str
    date: str
    type: str  # "income" or "expense"
    description: Optional[str] = None

# Rate limiting setup
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        
    async def check_rate_limit(self, user_id: int, max_requests: int = 5):
        now = datetime.utcnow()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time >= day_start
        ]
        
        if len(self.requests[user_id]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again tomorrow."
            )
            
        self.requests[user_id].append(now)
        return True

rate_limiter = RateLimiter()

async def get_ai_prediction(prompt: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return response.json()

async def format_transaction_data(transactions: List[FinancialTransaction]) -> Dict:
    if not transactions:
        raise HTTPException(status_code=404, detail="No transaction history found")
    
    monthly_data = {}
    for tx in transactions:
        month_key = tx.date.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expenses": 0}
        if tx.type == "income":
            monthly_data[month_key]["income"] += tx.amount
        else:
            monthly_data[month_key]["expenses"] += tx.amount
    return monthly_data

async def analyze_spending_categories(transactions: List[FinancialTransaction]) -> dict:
    categories = defaultdict(float)
    for tx in transactions:
        if tx.type == "expense":
            categories[tx.category] += tx.amount
    return dict(categories)

async def validate_financial_history(user_id: int, db: Session) -> bool:
    six_months_ago = datetime.now().date() - timedelta(days=180)
    query = select(FinancialTransaction).where(
        FinancialTransaction.user_id == user_id,
        FinancialTransaction.date >= six_months_ago
    )
    transactions = db.exec(query).all()
    return len(transactions) > 0

openrouter = OpenRouterService()

@app.post("/api/v1/forecast/expenses")
async def predict_expenses(user_id: int, db: Session = Depends(get_db)):
    # Get last 6 months of transactions
    six_months_ago = datetime.now().date() - timedelta(days=180)
    query = select(FinancialTransaction).where(
        FinancialTransaction.user_id == user_id,
        FinancialTransaction.date >= six_months_ago
    )
    transactions = db.exec(query).all()
    
    # Format historical data
    try:
        monthly_data = await format_transaction_data(transactions)
    except HTTPException as e:
        return {"error": str(e.detail), "predictions": None}

    # Get AI prediction
    try:
        prediction = await openrouter.make_request(
            template_name="expense_prediction",
            history=json.dumps(monthly_data)
        )
        return {
            "historical_data": monthly_data,
            "predictions": prediction
        }
    except HTTPException as e:
        raise e

@app.post("/api/v1/forecast/cashflow")
@cache(expire=86400)  # 24 hours
async def predict_cashflow(
    request: CashFlowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Get expense predictions
    expense_prediction = await predict_expenses(user_id=request.user_id, db=db)
    if "error" in expense_prediction:
        raise HTTPException(status_code=400, detail="Could not get expense predictions")

    # Calculate daily average spend
    monthly_data = expense_prediction["historical_data"]
    total_expenses = sum(month["expenses"] for month in monthly_data.values())
    daily_average = total_expenses / (len(monthly_data) * 30)

    # Sum upcoming bills
    total_bills = sum(bill.amount for bill in request.upcoming_bills)

    # Create AI prompt for cash flow prediction
    prompt = f"""
    Calculate end-of-month balance from:
    Current balance: {request.current_balance}
    Daily average spend: {daily_average:.2f}
    Upcoming bills total: {total_bills}
    Predicted income: {expense_prediction['predictions'].get('predicted_income', 0)}
    Return only valid JSON format: {{
        "predicted_balance": float,
        "overspend_risk": bool,
        "daily_budget_suggestion": float
    }}
    """

    try:
        prediction = await get_ai_prediction(prompt)
        return {
            "current_balance": request.current_balance,
            "daily_average_spend": daily_average,
            "upcoming_bills": total_bills,
            "prediction": prediction,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/insights")
async def get_financial_insights(
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    # Get current and previous month transactions
    current_month = datetime.now().date().replace(day=1)
    previous_month = (current_month - timedelta(days=1)).replace(day=1)
    
    current_query = select(FinancialTransaction).where(
        FinancialTransaction.user_id == user_id,
        FinancialTransaction.date >= current_month
    )
    previous_query = select(FinancialTransaction).where(
        FinancialTransaction.user_id == user_id,
        FinancialTransaction.date >= previous_month,
        FinancialTransaction.date < current_month
    )
    
    current_transactions = db.exec(current_query).all()
    previous_transactions = db.exec(previous_query).all()
    
    # Analyze spending patterns
    current_categories = await analyze_spending_categories(current_transactions)
    previous_categories = await analyze_spending_categories(previous_transactions)
    
    current_total = sum(current_categories.values())
    previous_total = sum(previous_categories.values())
    
    # Create AI prompt
    prompt = f"""
    Generate 3 specific cost-cutting suggestions based on:
    Current month spending by category: {json.dumps(current_categories)}
    Previous month spending by category: {json.dumps(previous_categories)}
    Return only valid JSON format: {{
        "insights": [str, str, str],
        "comparison": {{
            "current_total": {current_total},
            "previous_total": {previous_total},
            "percent_change": {((current_total - previous_total) / previous_total) * 100 if previous_total else 0}
        }}
    }}
    """
    
    try:
        ai_response = await get_ai_prediction(prompt)
        
        # Store insights in database
        insight = FinancialInsight(
            user_id=user_id,
            insights=ai_response["insights"],
            category_distribution=current_categories,
            month_comparison={
                "current": current_total,
                "previous": previous_total
            }
        )
        db.add(insight)
        await db.commit()
        
        return {
            "insights": ai_response["insights"],
            "spending_analysis": {
                "categories": current_categories,
                "comparison": ai_response["comparison"]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@app.post("/api/v1/loan/prediction")
async def predict_loan_eligibility(
    request: LoanPredictionRequest,
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    # Check rate limit
    await rate_limiter.check_rate_limit(user_id)
    
    # Validate financial history
    if not await validate_financial_history(user_id, db):
        raise HTTPException(
            status_code=400,
            detail="Insufficient financial history. Minimum 6 months required."
        )
    
    # Calculate debt ratio
    total_debt = sum(request.existing_loans)
    debt_ratio = (total_debt / request.monthly_income) * 100 if request.monthly_income > 0 else 100
    
    prompt = f"""
    Estimate loan eligibility score (0-1000) considering:
    Monthly savings: ${request.monthly_savings}
    Debt ratio: {debt_ratio:.2f}%
    Payment history: {request.payment_history_percent}%
    Credit score: {request.credit_score}
    Monthly income: ${request.monthly_income}
    
    Return only valid JSON format: {{
        "score": int,
        "reasons": [str, str],
        "improvement_tips": [str, str],
        "max_suggested_loan": float,
        "risk_level": str
    }}
    """
    
    try:
        prediction = await get_ai_prediction(prompt)
        return {
            "loan_eligibility": prediction,
            "financial_metrics": {
                "debt_ratio": debt_ratio,
                "monthly_savings_rate": (request.monthly_savings / request.monthly_income) * 100,
                "credit_score": request.credit_score
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/transactions")
async def add_transaction(
    transaction: TransactionCreate,
    user_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    try:
        new_transaction = FinancialTransaction(
            user_id=user_id,
            amount=transaction.amount,
            category=transaction.category,
            date=datetime.strptime(transaction.date, "%Y-%m-%d").date(),
            type=transaction.type
        )
        db.add(new_transaction)
        await db.commit()
    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to store transaction: {str(e)}")
    except ValueError as e:
        raise ValidationError(f"Invalid transaction data: {str(e)}")
    
    return {"status": "success", "transaction": new_transaction}

@app.get("/api/v1/transactions")
async def get_transactions(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    query = select(FinancialTransaction).where(FinancialTransaction.user_id == user_id)
    
    if start_date:
        query = query.where(FinancialTransaction.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.where(FinancialTransaction.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
    
    transactions = db.exec(query).all()
    return {"transactions": transactions}

@app.post("/api/v1/sample-data")
async def create_sample_data(
    user_id: int,
    months: int = 6,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    sample_transactions = generate_sample_transactions(user_id, months)
    
    for tx_data in sample_transactions:
        transaction = FinancialTransaction(**tx_data)
        db.add(transaction)
    
    await db.commit()
    return {
        "status": "success",
        "message": f"Created {len(sample_transactions)} sample transactions"
    }

@app.post("/predict/expenses")
async def predict_expenses(transactions: List[Transaction]):
    prompt = f"Predict monthly expenses based on: {transactions}"
    return await get_ai_prediction(prompt)

@app.post("/predict/cashflow")
async def predict_cashflow(transactions: List[Transaction]):
    prompt = f"Analyze cash flow patterns for: {transactions}"
    return await get_ai_prediction(prompt)

@app.post("/predict/loan")
async def predict_loan_approval(income: float, credit_score: int):
    prompt = f"Predict loan approval chances for income: {income}, credit: {credit_score}"
    return await get_ai_prediction(prompt)
