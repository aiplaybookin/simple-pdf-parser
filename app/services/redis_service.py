"""Redis operations service."""
import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations."""

    def __init__(self):
        self.client = None

    async def connect(self):
        """Connect to Redis."""
        self.client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        return self.client

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def add_task_to_stream(
        self,
        task_id: str,
        mode: str,
        files_data: list
    ) -> str:
        """Add task to Redis Stream."""
        import json
        task_message = {
            'task_id': task_id,
            'mode': mode,
            'files_data': json.dumps(files_data)
        }
        # This will be called from routes, which has access to redis_client
        return task_id


settings = Settings()
