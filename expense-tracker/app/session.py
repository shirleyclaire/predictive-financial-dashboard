from redis import Redis
from uuid import uuid4
import json
from datetime import datetime, timedelta

class RedisSessionStore:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:"
        self.expire_time = 3600  # 1 hour

    async def create_session(self, user_id: int, data: dict) -> str:
        session_id = str(uuid4())
        key = f"{self.prefix}{session_id}"
        
        session_data = {
            "user_id": user_id,
            "data": data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.redis.set(
            key,
            json.dumps(session_data),
            ex=self.expire_time
        )
        return session_id

    async def get_session(self, session_id: str) -> dict:
        key = f"{self.prefix}{session_id}"
        data = self.redis.get(key)
        if data:
            # Extend session on access
            self.redis.expire(key, self.expire_time)
            return json.loads(data)
        return None

    async def delete_session(self, session_id: str):
        key = f"{self.prefix}{session_id}"
        self.redis.delete(key)
