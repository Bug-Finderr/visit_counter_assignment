import redis
import asyncio
from typing import Dict, List, Optional
from .consistent_hash import ConsistentHash
from .config import settings


class RedisManager:
    def __init__(self):
        self.connection_pools: Dict[str, redis.ConnectionPool] = {}
        self.redis_clients: Dict[str, redis.Redis] = {}

        redis_nodes: List[str] = [
            node.strip() for node in settings.REDIS_NODES.split(",") if node.strip()
        ]

        self.consistent_hash = ConsistentHash(redis_nodes, settings.VIRTUAL_NODES)

        for node in redis_nodes:
            self.connection_pools[node] = redis.ConnectionPool.from_url(
                node,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                # stuck shard is treated as down instead of hanging the request
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
            )
            self.redis_clients[node] = redis.Redis(connection_pool=self.connection_pools[node])

    async def get_connection(self, key: str) -> redis.Redis:
        """Get the client that owns this key"""
        node = self.consistent_hash.get_node(key)
        return self.redis_clients[node]

    async def increment(self, key: str, amount: int = 1) -> int:
        """HINCRBY, retried over the timeout window"""
        client = await self.get_connection(key)

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                return await asyncio.to_thread(client.hincrby, "visit_count", key, amount)
            except redis.RedisError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (2**attempt))

        return 0

    async def get(self, key: str) -> Optional[int]:
        """HGET, returns the count or 0 when the key is new"""
        client = await self.get_connection(key)

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                value = await asyncio.to_thread(client.hget, "visit_count", key)
                return int(value) if value else 0
            except redis.RedisError:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(retry_delay * (2**attempt))

        return 0

    def get_node_for_key(self, key: str) -> str:
        """Node url the hash ring maps this key to"""
        return self.consistent_hash.get_node(key)

    def unreachable_nodes(self) -> List[str]:
        down = []
        for node, client in self.redis_clients.items():
            try:
                client.ping()
            except redis.RedisError:
                down.append(node)
        return down
