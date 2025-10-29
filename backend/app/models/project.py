"""
Project database model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class ProjectVisibility(str, enum.Enum):
    """Project visibility options"""
    PUBLIC = "public"
    PRIVATE = "private"


class Project(Base):
    """
    Project model representing a chip design project
    Each project has a Git repository and can run build/simulation jobs
    """
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Visibility control
    visibility = Column(
        Enum(ProjectVisibility),
        default=ProjectVisibility.PRIVATE,
        nullable=False
    )
    
    # Git repository information
    repo_url = Column(String, nullable=True)
    git_branch = Column(String, default="main")
    
    # Owner relationship
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="projects")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
