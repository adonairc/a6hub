"""
WebSocket routes for real-time build progress
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.websocket.manager import manager
from app.db.session import get_db
from app.models.job import Job
from app.models.user import User
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)
router = APIRouter()

security = HTTPBearer()


async def get_current_user_ws(
    token: str,
    db: Session = Depends(get_db)
) -> User:
    """Get current user from WebSocket token parameter"""
    try:
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return user
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.websocket("/ws/builds/{job_id}")
async def websocket_build_progress(
    websocket: WebSocket,
    job_id: int,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for receiving real-time build progress updates

    Query params:
        token: JWT authentication token

    Message format:
        {
            "job_id": int,
            "type": "status" | "progress" | "log" | "complete" | "error",
            "status": str,  # For status updates
            "message": str,  # For log messages
            "progress": float,  # 0-100 for progress updates
            "step": str,  # Current build step
            "timestamp": str
        }
    """
    # Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authenticate user if token provided
    if token:
        try:
            user = await get_current_user_ws(token, db)
            # Verify user has access to this job
            if job.user_id != user.id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Connect WebSocket
    await manager.connect(websocket, job_id)

    try:
        # Send initial status
        await websocket.send_json({
            "job_id": job_id,
            "type": "connected",
            "status": job.status.value,
            "message": f"Connected to job {job_id}"
        })

        # Keep connection alive and listen for client messages (if any)
        while True:
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed (e.g., pause/cancel)
                logger.debug(f"Received from client: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error receiving WebSocket message: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)
        logger.info(f"WebSocket closed for job {job_id}")
