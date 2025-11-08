"""
WebSocket connection manager for real-time build updates
"""
from fastapi import WebSocket
from typing import Dict, Set
import logging
import asyncio
import json
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates"""

    def __init__(self):
        # Store active connections per job_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.redis: aioredis.Redis = None

    async def connect(self, websocket: WebSocket, job_id: int):
        """Accept WebSocket connection and subscribe to job updates"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket, job_id: int):
        """Remove WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

            logger.info(f"WebSocket disconnected for job {job_id}")

    async def broadcast_to_job(self, job_id: int, message: dict):
        """Broadcast message to all connections for a specific job"""
        if job_id not in self.active_connections:
            return

        # Create a copy to avoid modification during iteration
        connections = list(self.active_connections[job_id])

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket for job {job_id}: {e}")
                self.disconnect(connection, job_id)

    async def get_redis(self):
        """Get or create Redis connection"""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis

    async def subscribe_to_job_updates(self, job_id: int):
        """Subscribe to Redis pub/sub for job updates and broadcast to WebSocket clients"""
        redis = await self.get_redis()
        channel_name = f"job:{job_id}:updates"

        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)

            logger.info(f"Subscribed to Redis channel: {channel_name}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.broadcast_to_job(job_id, data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")

                # Stop listening if no more connections
                if job_id not in self.active_connections:
                    logger.info(f"No more connections for job {job_id}, unsubscribing")
                    await pubsub.unsubscribe(channel_name)
                    break

        except Exception as e:
            logger.error(f"Error in Redis subscription for job {job_id}: {e}")
        finally:
            await pubsub.close()


# Global connection manager instance
manager = ConnectionManager()
