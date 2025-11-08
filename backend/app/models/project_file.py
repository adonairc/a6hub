"""
ProjectFile database model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ProjectFile(Base):
    """
    File within a project

    Files are now stored in MinIO object storage.
    Each file can contain multiple design modules that are extracted and stored separately.
    """

    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)  # Relative path within project

    # MinIO storage reference
    minio_bucket = Column(String, nullable=True)  # MinIO bucket name
    minio_key = Column(String, nullable=True)  # Object key in MinIO

    # Legacy support - content field kept for backward compatibility
    # New files should use MinIO storage
    content = Column(Text, nullable=True)  # Deprecated - use MinIO
    use_minio = Column(Boolean, default=True)  # Whether file uses MinIO storage

    # File metadata
    size_bytes = Column(Integer, default=0)
    mime_type = Column(String, default="text/plain")

    # SHA256 hash for content verification
    content_hash = Column(String, nullable=True)

    # Project relationship
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project = relationship("Project", back_populates="files")

    # Modules relationship - files can contain multiple modules
    modules = relationship("Module", back_populates="file", cascade="all, delete-orphan")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProjectFile(id={self.id}, filename={self.filename}, project_id={self.project_id})>"
