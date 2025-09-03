"""Event Bus for Redis Pub/Sub communication between workers and API."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Union

import redis.asyncio as redis

# Import metrics if available (API context)
try:
    from api.tracing import record_redis_failure
except ImportError:
    # Workers context - use dummy function
    def record_redis_failure(tenant: str, topic: str):
        pass


logger = logging.getLogger(__name__)


class EventBus:
    """Redis-based event bus for inter-service communication."""

    def __init__(self, redis_url: Union[str, None] = None):
        """Initialize Event Bus.

        Args:
            redis_url: Redis connection URL. Defaults to REDIS_URL env var.
        """
        self.redis_url = redis_url or "redis://localhost:6379"
        self._redis: Optional[redis.Redis] = None
        self._subscribers: Dict[str, asyncio.Task] = {}

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection, creating if needed."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url)
        return self._redis

    async def publish_event(self, topic: str, payload: Dict[str, Any]) -> bool:
        """Publish event to Redis channel.

        Args:
            topic: Redis channel name (e.g., "tenant123.jobs")
            payload: Event data

        Returns:
            True if published successfully
        """
        try:
            redis = await self._get_redis()

            # Extract tenant_id from topic
            tenant_id = topic.split(".")[0] if "." in topic else None

            # Add timestamp and tenant_id if not present
            if "ts" not in payload:
                payload["ts"] = datetime.now(timezone.utc).isoformat()
            if "tenant_id" not in payload and tenant_id:
                payload["tenant_id"] = tenant_id

            # Publish to Redis channel
            await redis.publish(topic, json.dumps(payload))
            logger.debug(f"Published event to {topic}: {payload}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            # Record failure metric
            tenant_id = topic.split(".")[0] if "." in topic else "unknown"
            record_redis_failure(tenant_id, topic)
            return False

    async def subscribe_loop(
        self, topic: str, handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Subscribe to Redis channel and process messages in loop.

        Args:
            topic: Redis channel name to subscribe to
            handler: Async function to handle received messages
        """
        try:
            redis = await self._get_redis()
            pubsub = redis.pubsub()

            await pubsub.subscribe(topic)
            logger.info(f"Subscribed to {topic}")

            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            payload = json.loads(message["data"])
                            await handler(payload)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in message: {e}")
                        except Exception as e:
                            logger.error(f"Handler error for message: {e}")

            except Exception as e:
                logger.error(f"Subscription loop error for {topic}: {e}")

            finally:
                await pubsub.unsubscribe(topic)
                await pubsub.close()

        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for Redis connection."""
        redis = await self._get_redis()
        try:
            yield redis
        finally:
            pass  # Don't close here, let the main instance manage it


# Global instance
event_bus = EventBus()


# Convenience functions
async def publish_event(topic: str, payload: Dict[str, Any]) -> bool:
    """Publish event to topic."""
    return await event_bus.publish_event(topic, payload)


def publish_event_sync(topic: str, payload: Dict[str, Any]) -> bool:
    """Synchronous version of publish_event for use in Celery tasks.

    Note: Celery tasks run outside an event loop, so we need to create one.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(event_bus.publish_event(topic, payload))
        return result
    except Exception as e:
        logger.error(f"Failed to publish event synchronously to {topic}: {e}")
        return False
    finally:
        loop.close()


async def subscribe_loop(topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """Subscribe to topic with handler."""
    return await event_bus.subscribe_loop(topic, handler)
