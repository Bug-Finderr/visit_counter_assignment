import redis
from typing import List
from .config import settings


class RedisManager:
    def __init__(self):
        """Init redis client using first redis node"""
        redis_nodes: List[str] = [
            node.strip() for node in settings.REDIS_NODES.split(",") if node.strip()
        ]
        self.redis_client = redis.Redis.from_url(redis_nodes[0])

    def increment(self, page_id: str, amount: int = 1) -> int:
        return self.redis_client.hincrby("visit_count", page_id, amount)  # type: ignore

    def get(self, page_id: str) -> int:
        count = self.redis_client.hget("visit_count", page_id)  # type: ignore
        return int(count) if count else 0
