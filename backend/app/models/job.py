"""
Job database model for build and simulation tasks
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class JobType(str, enum.Enum):
    """Types of jobs that can be executed"""
    SIMULATION = "simulation"
    BUILD = "build"
    SYNTHESIS = "synthesis"
    PLACE_ROUTE = "place_route"


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    """
    Job model representing build/simulation tasks
    Tracks Celery task execution and stores results
    """
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Job identification
    celery_task_id = Column(String, unique=True, index=True, nullable=True)
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    # Job configuration
    config = Column(JSON, nullable=True)  # Job-specific configuration
    
    # Execution details
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    artifacts_path = Column(String, nullable=True)  # Path in MinIO

    # Progress tracking
    current_step = Column(String, nullable=True)  # Current build step being executed
    progress_data = Column(JSON, nullable=True)  # Structured progress info (steps completed, percentages, etc.)
    
    # Relationships
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="jobs")
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="jobs")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"
