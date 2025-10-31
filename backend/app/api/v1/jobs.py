"""
Jobs API endpoints
Handles creation and management of build/simulation jobs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.job import Job, JobStatus, JobType
from app.schemas.job import (
    JobCreate,
    JobResponse,
    JobListItem,
    JobLogsResponse
)

router = APIRouter()


def check_project_access(project: Project, user: User):
    """Check if user has access to project"""
    if project.owner_id != user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.post("/{project_id}/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    project_id: int,
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job
    
    - Creates simulation or build job for project
    - Job is queued for execution by Celery workers
    - Only project owner can create jobs
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Only owner can create jobs
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can create jobs"
        )
    
    # Create new job
    new_job = Job(
        job_type=job_data.job_type,
        status=JobStatus.PENDING,
        config=job_data.config,
        project_id=project_id,
        user_id=current_user.id
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # TODO: Queue job in Celery
    # task = execute_job.delay(new_job.id)
    # new_job.celery_task_id = task.id
    # db.commit()
    
    return new_job


@router.get("/{project_id}/jobs", response_model=List[JobListItem])
async def list_project_jobs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all jobs for a project
    
    - Returns list of jobs with basic info
    - User must have read access to project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user)
    
    jobs = (
        db.query(Job)
        .filter(Job.project_id == project_id)
        .order_by(Job.created_at.desc())
        .all()
    )
    
    return jobs


@router.get("/{project_id}/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    project_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job details
    
    - Returns full job information including logs
    - User must have read access to project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user)
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.project_id == project_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.get("/{project_id}/jobs/{job_id}/logs", response_model=JobLogsResponse)
async def get_job_logs(
    project_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job logs
    
    - Returns current job logs and status
    - User must have read access to project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user)
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.project_id == project_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobLogsResponse(
        job_id=job.id,
        logs=job.logs or "",
        status=job.status,
        current_step=job.current_step,
        progress_data=job.progress_data
    )


@router.delete("/{project_id}/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    project_id: int,
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a running job
    
    - Stops job execution if still running
    - Only project owner can cancel jobs
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Only owner can cancel jobs
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can cancel jobs"
        )
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.project_id == project_id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Can only cancel pending or running jobs
    if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not running"
        )
    
    # Update job status
    job.status = JobStatus.CANCELLED
    
    # TODO: Cancel Celery task
    # if job.celery_task_id:
    #     celery_app.control.revoke(job.celery_task_id, terminate=True)
    
    db.commit()
    
    return None
