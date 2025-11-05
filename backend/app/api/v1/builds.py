"""
Builds API endpoints for LibreLane flow management
Handles build configuration, presets, and flow orchestration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.job import Job, JobType, JobStatus
from app.schemas.librelane import (
    LibreLaneFlowConfig,
    LibreLaneBuildRequest,
    LibreLaneBuildStatus,
    LibreLaneFlowPreset,
    LIBRELANE_PRESETS,
    PDKType
)
from app.schemas.job import JobCreate, JobResponse
from app.workers.tasks import run_build

router = APIRouter()


@router.get("/presets", response_model=Dict[str, LibreLaneFlowPreset])
async def get_build_presets():
    """
    Get available LibreLane flow presets

    Returns common configuration presets for different use cases:
    - minimal: Fast flow for testing
    - balanced: Balance between speed and quality
    - high_quality: Maximum quality for tape-out
    """
    return LIBRELANE_PRESETS


@router.get("/pdks", response_model=List[str])
async def get_available_pdks():
    """
    Get list of available Process Design Kits (PDKs)

    Returns supported PDK options for ASIC builds
    """
    return [pdk.value for pdk in PDKType]


@router.post("/{project_id}/build", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def start_build(
    project_id: int,
    build_request: LibreLaneBuildRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a LibreLane ASIC build for a project

    - Creates a build job with the specified flow configuration
    - Executes LibreLane in a Docker container
    - Returns job information for status tracking
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is owner
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can start builds"
        )

    # Check if project has files
    if not project.files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no files. Upload Verilog files before building."
        )

    # Convert LibreLaneFlowConfig to dict for storage
    config_dict = build_request.config.model_dump()

    # Create job
    job = Job(
        job_type=JobType.BUILD,
        status=JobStatus.PENDING,
        config=config_dict,
        project_id=project_id,
        user_id=current_user.id
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue Celery task
    task = run_build.delay(job.id)

    # Update job with celery task ID
    job.celery_task_id = task.id
    db.commit()
    db.refresh(job)

    return job


@router.get("/{project_id}/build/config", response_model=LibreLaneFlowConfig)
async def get_build_config(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the last used build configuration for a project

    - Returns the configuration from the most recent build job
    - Falls back to default configuration if no previous builds
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check access
    if project.owner_id != current_user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get most recent build job
    last_build = (
        db.query(Job)
        .filter(Job.project_id == project_id, Job.job_type == JobType.BUILD)
        .order_by(Job.created_at.desc())
        .first()
    )

    if last_build and last_build.config:
        # Return last used configuration
        return LibreLaneFlowConfig(**last_build.config)
    else:
        # Return default configuration with project-specific values
        # Auto-detect all Verilog/SystemVerilog files
        verilog_extensions = ('.v', '.sv', '.vh')
        verilog_files = [f.filepath for f in project.files if f.filepath.endswith(verilog_extensions)]

        return LibreLaneFlowConfig(
            design_name=project.name,
            verilog_files=verilog_files,  # Empty list will trigger auto-detection in worker
        )


@router.put("/{project_id}/build/config", response_model=Dict[str, str])
async def save_build_config(
    project_id: int,
    config: LibreLaneFlowConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save build configuration for a project (for future reference)

    Note: This doesn't create a job, just validates and stores the config.
    Use POST /{project_id}/build to actually start a build.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is owner
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can save build configuration"
        )

    # Configuration is validated by Pydantic
    # In a real implementation, you might store this in a separate table
    # For now, we'll just validate it

    return {
        "message": "Build configuration is valid",
        "design_name": config.design_name,
        "pdk": config.pdk
    }


@router.get("/{project_id}/build/status", response_model=LibreLaneBuildStatus)
async def get_build_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of the latest build for a project

    - Returns status of most recent build job
    - Includes progress information if available
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check access
    if project.owner_id != current_user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get most recent build job
    latest_build = (
        db.query(Job)
        .filter(Job.project_id == project_id, Job.job_type == JobType.BUILD)
        .order_by(Job.created_at.desc())
        .first()
    )

    if not latest_build:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No build jobs found for this project"
        )

    return LibreLaneBuildStatus(
        job_id=latest_build.id,
        status=latest_build.status.value,
        current_step=latest_build.current_step,
        progress_data=latest_build.progress_data,
        logs=latest_build.logs
    )
