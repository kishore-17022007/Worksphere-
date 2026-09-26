"""Redis client configuration for application services."""

from redis.asyncio import Redis

from app.core.config import get_settings


def create_redis() -> Redis:
    """Create an async Redis client from the application settings."""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


redis_client = create_redis()
