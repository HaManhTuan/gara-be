"""Redis client for caching and OTP storage"""

from typing import Optional

import redis.asyncio as aioredis

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("redis-client")


class RedisClient:
    """Redis client wrapper for async operations"""

    def __init__(self) -> None:
        """Initialize Redis client"""
        self._client: Optional[aioredis.Redis] = None

    async def get_client(self) -> aioredis.Redis:
        """
        Get or create Redis client
        
        Returns:
            Redis client instance
        """
        if self._client is None:
            self._client = await aioredis.from_url(
                settings.CELERY_BROKER_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            logger.info("Redis client initialized")
        return self._client

    async def set(
        self,
        key: str,
        value: str,
        expiry_seconds: Optional[int] = None
    ) -> bool:
        """
        Set a key-value pair in Redis
        
        Args:
            key: Redis key
            value: Value to store
            expiry_seconds: Expiry time in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            client = await self.get_client()
            if expiry_seconds:
                await client.setex(key, expiry_seconds, value)
            else:
                await client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Value if exists, None otherwise
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            return value
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis
        
        Args:
            key: Redis key
            
        Returns:
            True if key was deleted
        """
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis
        
        Args:
            key: Redis key
            
        Returns:
            True if key exists
        """
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key
        
        Args:
            key: Redis key
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        try:
            client = await self.get_client()
            return await client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {str(e)}")
            return -2

    async def close(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis client closed")
            self._client = None


# Create singleton instance
redis_client = RedisClient()
