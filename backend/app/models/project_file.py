"""
ProjectFile database model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectFile(Base):
    """
    File within a project
    Stores file metadata and content for HDL files, testbenches, and configurations
    """
    
    __tablename__ = "project_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)  # Relative path within project
    content = Column(Text, nullable=True)  # File content for text files
    size_bytes = Column(Integer, default=0)
    mime_type = Column(String, default="text/plain")
    
    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="files")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectFile(id={self.id}, filename={self.filename}, project_id={self.project_id})>"
