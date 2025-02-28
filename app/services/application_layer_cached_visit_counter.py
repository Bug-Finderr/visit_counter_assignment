import asyncio
import time
from typing import Dict, Tuple
from app.core.simple_redis_manager import RedisManager


class VisitCounterService:
    # static cache shared across all instances
    _cache: Dict[str, Tuple[int, float]] = {}
    _cache_ttl = 5.0

    def __init__(self):
        self.redis_manager = RedisManager()
        self.served_via = "redis"  # default src

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page, writing directly to Redis
        """
        await asyncio.to_thread(self.redis_manager.increment, page_id)
        if page_id in self.__class__._cache:
            del self.__class__._cache[page_id]

    async def get_visit_count(self, page_id: str) -> int:
        """
        Get visit count from cache or Redis if cache expired/missing
        """
        current_time = time.time()

        # check if in cache and !expired
        if page_id in self.__class__._cache:
            count, timestamp = self.__class__._cache[page_id]
            if current_time - timestamp < self.__class__._cache_ttl:
                self.served_via = "in_memory"
                return count

        # cache miss or expired, get from redis
        self.served_via = "redis"
        count = await asyncio.to_thread(self.redis_manager.get, page_id)

        self.__class__._cache[page_id] = (count, current_time)
        return count

    def get_served_via(self) -> str:
        """Get the source of the last retrieved value (in_memory or redis)"""
        return self.served_via
