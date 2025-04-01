from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import httpx
import os
from datetime import datetime, timedelta
from fastapi import HTTPException
import json
import asyncio
from collections import defaultdict
from shared.config import get_settings

class OpenRouterResponse(BaseModel):
    id: str
    choices: List[Dict]
    model: str
    created: int
    response_ms: Optional[int]

class PromptTemplate:
    def __init__(self, template: str, required_vars: List[str]):
        self.template = template
        self.required_vars = required_vars
    
    def format(self, **kwargs):
        missing = [var for var in self.required_vars if var not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        return self.template.format(**kwargs)

class OpenRouterService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENROUTER_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.requests = defaultdict(list)
        self.rate_limit = 50  # requests per minute
        self.templates = {
            "expense_prediction": PromptTemplate(
                """Analyze spending patterns and predict expenses:
                History: {history}
                Return JSON: {{"predicted_amount": float, "confidence": float}}""",
                ["history"]
            ),
            "loan_eligibility": PromptTemplate(
                """Evaluate loan eligibility:
                Income: {income}
                Credit Score: {credit_score}
                Return JSON: {{"score": int, "risk_level": str}}""",
                ["income", "credit_score"]
            )
        }
    
    async def check_rate_limit(self):
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        self.requests["calls"] = [
            time for time in self.requests["calls"] 
            if time > minute_ago
        ]
        
        if len(self.requests["calls"]) >= self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        self.requests["calls"].append(now)

    async def make_request(self, prompt: str, template_name: Optional[str] = None, **kwargs):
        await self.check_rate_limit()
        
        if template_name:
            if template_name not in self.templates:
                raise ValueError(f"Unknown template: {template_name}")
            prompt = self.templates[template_name].format(**kwargs)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-7b-instruct",
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                validated_response = OpenRouterResponse(**data)
                return json.loads(validated_response.choices[0]["message"]["content"])
                
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"API request failed: {str(e)}"
                )
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail="Invalid JSON response from API"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Prediction failed: {str(e)}"
                )

    def add_template(self, name: str, template: str, required_vars: List[str]):
        self.templates[name] = PromptTemplate(template, required_vars)
