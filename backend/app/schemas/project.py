"""
Pydantic schemas for Project model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectVisibility


# Project Creation
class ProjectCreate(BaseModel):
    """Schema for creating a new project"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    git_branch: str = "main"


# Project Update
class ProjectUpdate(BaseModel):
    """Schema for updating project details"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    visibility: Optional[ProjectVisibility] = None
    git_branch: Optional[str] = None


# Project Response
class ProjectResponse(BaseModel):
    """Schema for project data in responses"""
    id: int
    name: str
    slug: str
    description: Optional[str]
    visibility: ProjectVisibility
    git_branch: str
    owner_id: int
    stars_count: int = 0
    views_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# Project List Item (minimal info for lists)
class ProjectListItem(BaseModel):
    """Schema for project in list views"""
    id: int
    name: str
    slug: str
    description: Optional[str]
    visibility: ProjectVisibility
    owner_id: int
    stars_count: int = 0
    views_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# Project File Schema
class ProjectFileCreate(BaseModel):
    """Schema for creating/uploading a file"""
    filename: str
    filepath: str
    content: Optional[str] = None
    mime_type: str = "text/plain"


class ProjectFileUpdate(BaseModel):
    """Schema for updating a file"""
    content: Optional[str] = None
    filename: Optional[str] = None


class ProjectFileResponse(BaseModel):
    """Schema for file data in responses"""
    id: int
    filename: str
    filepath: str
    size_bytes: int
    mime_type: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}


class ProjectFileWithContent(ProjectFileResponse):
    """Schema for file with full content"""
    content: Optional[str]
