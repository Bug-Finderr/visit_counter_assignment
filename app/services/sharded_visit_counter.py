from urllib.parse import urlparse
from app.core.sharded_redis_manager import RedisManager


class VisitCounterService:
    def __init__(self, redis_manager: RedisManager | None = None):
        self.redis_manager = redis_manager or RedisManager()
        self.last_used_node = None

    async def increment_visit(self, page_id: str) -> None:
        """Increment visit count for a page"""
        await self.redis_manager.increment(page_id)
        self.last_used_node = self.redis_manager.get_node_for_key(page_id)

    async def get_visit_count(self, page_id: str) -> int:
        """Get current visit count for a page"""
        count = await self.redis_manager.get(page_id)
        self.last_used_node = self.redis_manager.get_node_for_key(page_id)
        return count if count else 0

    def get_served_via(self) -> str:
        """Short host name of the shard that answered last, e.g. visit-counter-redis-1"""
        if self.last_used_node:
            return urlparse(self.last_used_node).hostname.split(".")[0]
        return "redis"
