"""
Main API router - combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, files, jobs, builds

api_router = APIRouter()

# Include all routers with their prefixes and tags
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    files.router,
    prefix="/projects",
    tags=["files"]
)

api_router.include_router(
    jobs.router,
    prefix="/projects",
    tags=["jobs"]
)

api_router.include_router(
    builds.router,
    prefix="/builds",
    tags=["builds"]
)
