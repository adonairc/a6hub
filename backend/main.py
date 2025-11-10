"""
a6hub - Main FastAPI Application
Multi-tenant SaaS platform for collaborative chip design automation
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import logging

from app.api.v1.router import api_router
from app.api.v1.websocket import router as websocket_router
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cloud-based platform for collaborative chip design automation",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include WebSocket routes
app.include_router(websocket_router, prefix=f"{settings.API_V1_STR}/ws", tags=["websocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and resources on startup"""
    logger.info("Starting a6hub backend...")
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    # Mount kweb as a sub-application
    try:
        from app.services.kweb_service import kweb_service
        from kweb.viewer import get_app as get_kweb_app

        kweb_app = get_kweb_app(fileslocation=kweb_service.temp_dir)
        app.mount("/kweb-internal", kweb_app)
        logger.info(f"Mounted kweb viewer at /kweb-internal, serving from: {kweb_service.temp_dir}")
    except ImportError as e:
        logger.warning(f"KWeb not available, skipping mount: {e}")
    except Exception as e:
        logger.error(f"Failed to mount kweb: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down a6hub backend...")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "a6hub API",
        "version": "0.1.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "a6hub-backend"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
