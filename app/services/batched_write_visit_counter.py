import asyncio
import time
import threading
from typing import Dict
from app.core.simple_redis_manager import RedisManager


class VisitCounterService:
    _visit_buffer: Dict[str, int] = {}
    _buffer_lock = asyncio.Lock()
    _flush_interval = 30.0
    _thread = None

    def __init__(self):
        self.redis_manager = RedisManager()
        self._start_background_flush()

    def _start_background_flush(self):
        """start bg flush thread if not running already"""
        if self.__class__._thread is None:
            self.__class__._thread = threading.Thread(
                target=self._periodic_flush, daemon=True
            )
            self.__class__._thread.start()

    def _periodic_flush(self):
        """bg thread worker that flushes every 30 seconds"""
        while True:
            time.sleep(self.__class__._flush_interval)
            # Use dedicated event loop for async operations in thread
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self._flush_buffer_to_redis())
            except Exception as e:
                print(f"Error flushing buffer: {e}")
            finally:
                loop.close()

    async def _flush_buffer_to_redis(self):
        """Flush all pending writes to Redis"""
        # quickly swap buffer with an empty one (minimal lock time)
        buffer_to_flush = {}
        async with self.__class__._buffer_lock:
            if self.__class__._visit_buffer:
                buffer_to_flush = self.__class__._visit_buffer.copy()
                self.__class__._visit_buffer.clear()

        # process outside lock
        for page_id, count in buffer_to_flush.items():
            await asyncio.to_thread(self.redis_manager.increment, page_id, count)

    async def increment_visit(self, page_id: str) -> None:
        """Increment visit count in memory buffer"""
        async with self.__class__._buffer_lock:
            self.__class__._visit_buffer[page_id] = (
                self.__class__._visit_buffer.get(page_id, 0) + 1
            )

    async def get_visit_count(self, page_id: str) -> int:
        """Get combined visit count from redis and memory buffer"""
        # extract any pending count for this page & remove from buffer
        pending_count = 0
        async with self.__class__._buffer_lock:
            pending_count = self.__class__._visit_buffer.pop(page_id, 0)

        if pending_count > 0:  # flush pending count to redis
            await asyncio.to_thread(
                self.redis_manager.increment, page_id, pending_count
            )

        redis_count = await asyncio.to_thread(self.redis_manager.get, page_id)

        async with self.__class__._buffer_lock:
            new_pending = self.__class__._visit_buffer.get(page_id, 0)

        return redis_count + new_pending
