import asyncio
from app.core.simple_redis_manager import RedisManager


class VisitCounterService:
    def __init__(self):
        self.redis_manager = RedisManager()

    async def increment_visit(self, page_id: str) -> None:
        """
        Increment visit count for a page stored in Redis
        """
        await asyncio.to_thread(self.redis_manager.increment, page_id)

    async def get_visit_count(self, page_id: str) -> int:
        """
        Get current visit count for a page from Redis
        """
        return await asyncio.to_thread(self.redis_manager.get, page_id)
