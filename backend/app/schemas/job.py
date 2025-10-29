"""
Pydantic schemas for Job model
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.job import JobType, JobStatus


# Job Creation
class JobCreate(BaseModel):
    """Schema for creating a new job"""
    job_type: JobType
    config: Optional[Dict[str, Any]] = None


# Job Response
class JobResponse(BaseModel):
    """Schema for job data in responses"""
    id: int
    celery_task_id: Optional[str]
    job_type: JobType
    status: JobStatus
    config: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    artifacts_path: Optional[str]
    project_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# Job List Item (minimal info)
class JobListItem(BaseModel):
    """Schema for job in list views"""
    id: int
    job_type: JobType
    status: JobStatus
    project_id: int
    created_at: datetime
    completed_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


# Job Status Update
class JobStatusUpdate(BaseModel):
    """Schema for updating job status"""
    status: JobStatus
    logs: Optional[str] = None
    error_message: Optional[str] = None
    artifacts_path: Optional[str] = None


# Job Logs Response
class JobLogsResponse(BaseModel):
    """Schema for streaming job logs"""
    job_id: int
    logs: str
    status: JobStatus
