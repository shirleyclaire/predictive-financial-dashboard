import pytest
import httpx
import asyncio
from datetime import datetime, timedelta
import jwt

BASE_URL = "http://localhost"
TEST_USER = {"email": "test@example.com", "password": "testpass123"}

@pytest.fixture
async def auth_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/expenses/token",
            data={"username": TEST_USER["email"], "password": TEST_USER["password"]}
        )
        return response.json()["access_token"]

@pytest.mark.asyncio
async def test_expense_prediction_flow(auth_token):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Add expense
        expense_data = {
            "amount": 100.0,
            "category": "groceries",
            "description": "Weekly groceries",
            "type": "expense"
        }
        response = await client.post(
            f"{BASE_URL}/api/expenses/transactions/",
            json=expense_data,
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify expense was added
        response = await client.get(
            f"{BASE_URL}/api/expenses/transactions/summary/monthly",
            headers=headers
        )
        assert response.status_code == 200
        summary = response.json()
        assert any(item["category"] == "groceries" for item in summary)
        
        # Check predictions are updated
        await asyncio.sleep(2)  # Wait for async processing
        response = await client.get(
            f"{BASE_URL}/api/predictions/predict/test_user",
            headers=headers
        )
        assert response.status_code == 200
        predictions = response.json()
        assert "predictions" in predictions
