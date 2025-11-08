"""
WebSocket connection manager for real-time build progress updates
"""
from typing import Dict, Set
from fastapi import WebSocket
import logging
import asyncio
import json
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Supports multiple connections per job and broadcasts messages to all connected clients.
    """

    def __init__(self):
        # Map of job_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.redis: aioredis.Redis = None
        self.pubsub = None
        self.listener_task = None

    async def connect(self, websocket: WebSocket, job_id: int):
        """Accept a new WebSocket connection for a specific job"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket, job_id: int):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            logger.info(f"WebSocket disconnected for job {job_id}. Remaining: {len(self.active_connections[job_id])}")

            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: int, message: dict):
        """Send a message to all connections for a specific job"""
        if job_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, job_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        for job_id in list(self.active_connections.keys()):
            await self.send_message(job_id, message)

    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub"""
        try:
            self.redis = await aioredis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("build_progress")
            logger.info("Redis pub/sub initialized for WebSocket manager")

            # Start listening for messages
            self.listener_task = asyncio.create_task(self._listen_for_messages())
        except Exception as e:
            logger.error(f"Failed to initialize Redis pub/sub: {e}")

    async def _listen_for_messages(self):
        """Listen for messages from Redis pub/sub and broadcast to WebSocket clients"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        job_id = data.get("job_id")

                        if job_id:
                            await self.send_message(job_id, data)
                            logger.debug(f"Broadcasted message to job {job_id}: {data.get('type')}")
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled")
        except Exception as e:
            logger.error(f"Error in Redis listener: {e}")

    async def close(self):
        """Clean up resources"""
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.unsubscribe("build_progress")
            await self.pubsub.close()

        if self.redis:
            await self.redis.close()

        logger.info("WebSocket manager closed")


# Global instance
manager = ConnectionManager()
