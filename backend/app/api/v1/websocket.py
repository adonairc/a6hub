"""
WebSocket API endpoints for real-time build updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging
import asyncio

from app.core.security import get_current_user_ws
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.websockets.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/jobs/{job_id}/updates")
async def job_updates_websocket(
    websocket: WebSocket,
    job_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time job updates

    Provides real-time updates for:
    - Job status changes
    - Build progress
    - Log output
    - Step transitions

    Query Parameters:
        token: JWT authentication token

    Message Format:
        {
            "type": "status" | "progress" | "log" | "step" | "complete" | "error",
            "data": {
                "status": "running",
                "progress": 45,
                "current_step": "synthesis",
                "log_line": "Running synthesis...",
                "error_message": "Build failed"
            },
            "timestamp": "2025-01-06T12:00:00Z"
        }
    """
    # Authenticate user via token
    try:
        user = await get_current_user_ws(token, db)
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Check if job exists and user has access
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    # Check access permissions
    if job.user_id != user.id:
        # Could also check project ownership/visibility here
        await websocket.close(code=4003, reason="Access denied")
        return

    # Accept connection
    await manager.connect(websocket, job_id)

    try:
        # Start Redis subscription task
        subscription_task = asyncio.create_task(
            manager.subscribe_to_job_updates(job_id)
        )

        # Send initial job state
        await websocket.send_json({
            "type": "connected",
            "data": {
                "job_id": job_id,
                "status": job.status.value,
                "current_step": job.current_step,
                "progress": job.progress_data.get("progress", 0) if job.progress_data else 0
            }
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (mainly for keep-alive)
                data = await websocket.receive_text()

                # Handle ping/pong for keep-alive
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for job {job_id}")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket receive loop: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)
        # Cancel subscription task if still running
        if 'subscription_task' in locals() and not subscription_task.done():
            subscription_task.cancel()
