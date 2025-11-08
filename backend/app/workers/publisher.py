"""
Redis publisher for real-time job updates
"""
import redis
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobUpdatePublisher:
    """Publishes job updates to Redis for WebSocket broadcasting"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def publish_update(self, job_id: int, update_type: str, data: Dict[str, Any]):
        """
        Publish job update to Redis channel

        Args:
            job_id: Job ID
            update_type: Type of update (status, progress, log, step, complete, error)
            data: Update data dictionary
        """
        channel = f"job:{job_id}:updates"

        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            self.redis_client.publish(channel, json.dumps(message))
            logger.debug(f"Published {update_type} update for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to publish update for job {job_id}: {e}")

    def publish_status(self, job_id: int, status: str):
        """Publish job status change"""
        self.publish_update(job_id, "status", {"status": status})

    def publish_progress(self, job_id: int, progress: int, current_step: str, completed_steps: list):
        """Publish progress update"""
        self.publish_update(job_id, "progress", {
            "progress": progress,
            "current_step": current_step,
            "completed_steps": completed_steps
        })

    def publish_log(self, job_id: int, log_line: str):
        """Publish log line"""
        self.publish_update(job_id, "log", {"log_line": log_line})

    def publish_step(self, job_id: int, step_name: str, step_label: str):
        """Publish step transition"""
        self.publish_update(job_id, "step", {
            "step_name": step_name,
            "step_label": step_label
        })

    def publish_complete(self, job_id: int, status: str, message: Optional[str] = None):
        """Publish job completion"""
        data = {"status": status}
        if message:
            data["message"] = message
        self.publish_update(job_id, "complete", data)

    def publish_error(self, job_id: int, error_message: str):
        """Publish error"""
        self.publish_update(job_id, "error", {"error_message": error_message})


# Global publisher instance
publisher = JobUpdatePublisher()
