from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import Optional, List
from shared.database import get_db, SavingsGoal
from services.auth_service import verify_token
import httpx
import os
import json
from sqlmodel import select, Session

app = FastAPI()

class SavingsGoal(BaseModel):
    target_amount: float
    current_amount: float
    target_date: datetime
    category: str
    description: Optional[str]

class GoalTrackingRequest(BaseModel):
    goal_id: int
    current_amount: float

async def get_ai_suggestion(prompt: str):
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

@app.post("/goals")
async def create_goal(goal: SavingsGoal, db=Depends(get_db)):
    # Add database operations here
    return {"status": "success", "goal": goal}

@app.get("/goals/{goal_id}")
async def get_goal(goal_id: int, db=Depends(get_db)):
    # Add database query here
    return {"goal_id": goal_id}

@app.put("/goals/{goal_id}/progress")
async def update_progress(goal_id: int, current_amount: float, db=Depends(get_db)):
    # Add progress update logic here
    return {"status": "updated", "goal_id": goal_id}

@app.post("/api/v1/savings/track")
async def track_savings_goal(
    request: GoalTrackingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    # Fetch goal
    goal = db.get(SavingsGoal, request.goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Calculate progress metrics
    days_remaining = (goal.deadline - date.today()).days
    total_days = (goal.deadline - goal.start_date).days
    daily_required = (goal.target_amount - request.current_amount) / days_remaining if days_remaining > 0 else 0
    progress_percent = (request.current_amount / goal.target_amount) * 100
    
    # Update progress history
    goal.progress_history.append({
        "date": datetime.utcnow().isoformat(),
        "amount": request.current_amount,
        "daily_required": daily_required
    })
    
    prompt = f"""
    Suggest adjustments to meet savings target of ${goal.target_amount} by {goal.deadline}.
    Current progress: {progress_percent:.1f}%
    Days remaining: {days_remaining}
    Daily savings required: ${daily_required:.2f}
    
    Return only valid JSON format: {{
        "daily_required": float,
        "projected_outcome": str,
        "suggestions": [str, str],
        "probability_of_success": float
    }}
    """
    
    try:
        ai_suggestion = await get_ai_suggestion(prompt)
        
        # Update goal
        goal.current_amount = request.current_amount
        goal.last_updated = datetime.utcnow()
        db.add(goal)
        await db.commit()
        
        return {
            "goal_progress": {
                "current_amount": request.current_amount,
                "target_amount": goal.target_amount,
                "progress_percent": progress_percent,
                "days_remaining": days_remaining
            },
            "analysis": ai_suggestion,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track progress: {str(e)}")
