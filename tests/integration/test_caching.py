import pytest
import redis
import httpx
import time

@pytest.fixture
def redis_client():
    return redis.Redis(host='localhost', port=6379, db=0)

@pytest.mark.asyncio
async def test_cache_invalidation(auth_token, redis_client):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get initial summary (should cache)
        response = await client.get(
            f"{BASE_URL}/api/expenses/transactions/summary/monthly",
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify cache exists
        cache_key = f"monthly_summary:test_user"
        assert redis_client.exists(cache_key)
        
        # Add new expense
        expense_data = {
            "amount": 50.0,
            "category": "utilities",
            "description": "Test expense",
            "type": "expense"
        }
        response = await client.post(
            f"{BASE_URL}/api/expenses/transactions/",
            json=expense_data,
            headers=headers
        )
        
        # Verify cache was invalidated
        assert not redis_client.exists(cache_key)
