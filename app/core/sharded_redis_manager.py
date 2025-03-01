import redis
import asyncio
from typing import Dict, List, Optional
from .consistent_hash import ConsistentHash
from .config import settings


class RedisManager:
    def __init__(self):
        """Initialize Redis connection pools and consistent hashing"""
        self.connection_pools: Dict[str, redis.ConnectionPool] = {}
        self.redis_clients: Dict[str, redis.Redis] = {}

        redis_nodes: List[str] = [
            node.strip() for node in settings.REDIS_NODES.split(",") if node.strip()
        ]

        self.consistent_hash = ConsistentHash(redis_nodes, settings.VIRTUAL_NODES)

        for node in redis_nodes:
            self.connection_pools[node] = redis.ConnectionPool.from_url(
                node, password=settings.REDIS_PASSWORD, db=settings.REDIS_DB
            )
            self.redis_clients[node] = redis.Redis(
                connection_pool=self.connection_pools[node]
            )

    async def get_connection(self, key: str) -> redis.Redis:
        """
        Get Redis connection for the given key using consistent hashing

        Args:
            key: The key to determine which Redis node to use

        Returns:
            Redis client for the appropriate node
        """
        node = self.consistent_hash.get_node(key)
        return self.redis_clients[node]

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis

        Args:
            key: The key to increment
            amount: Amount to increment by

        Returns:
            New value of the counter
        """
        client = await self.get_connection(key)

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                return client.hincrby("visit_count", key, amount)  # type: ignore
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(retry_delay * (2**attempt))

        return 0

    async def get(self, key: str) -> Optional[int]:
        """
        Get value for a key from Redis

        Args:
            key: The key to get

        Returns:
            Value of the key or None if not found
        """
        client = await self.get_connection(key)

        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                value = client.hget("visit_count", key)
                return int(value) if value else 0  # type: ignore
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(retry_delay * (2**attempt))

        return 0

    def get_node_for_key(self, key: str) -> str:
        """Get the Redis node that handles this key"""
        return self.consistent_hash.get_node(key)
