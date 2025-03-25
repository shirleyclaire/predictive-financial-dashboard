import redis
from typing import Optional, Any
import json
from datetime import datetime

class SmartCache:
    def __init__(self, host='redis', port=6379):
        self.redis = redis.Redis(
            host=host,
            port=port,
            connection_pool=redis.ConnectionPool(
                max_connections=20,
                host=host,
                port=port
            )
        )
        self.access_counts = {}

    async def get(self, key: str) -> Optional[Any]:
        # Track access patterns
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        value = self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, expiration: int = 3600):
        # Adjust expiration based on access frequency
        if self.access_counts.get(key, 0) > 10:
            expiration *= 2  # Double cache time for frequently accessed items
        
        self.redis.set(
            key,
            json.dumps(value),
            ex=expiration
        )

    async def get_or_set(self, key: str, fetch_func, expiration: int = 3600):
        value = await self.get(key)
        if value is None:
            value = await fetch_func()
            await self.set(key, value, expiration)
        return value

    def invalidate(self, pattern: str):
        for key in self.redis.scan_iter(pattern):
            self.redis.delete(key)
            self.access_counts.pop(key.decode('utf-8'), None)
