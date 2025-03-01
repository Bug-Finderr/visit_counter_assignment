from app.core.sharded_redis_manager import RedisManager


class VisitCounterService:
    def __init__(self):
        self.redis_manager = RedisManager()
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
        """Get the source of the last retrieved value"""
        if self.last_used_node:
            if "redis1" in self.last_used_node:
                return "redis_7070"
            elif "redis2" in self.last_used_node:
                return "redis_7071"
        return "redis"
