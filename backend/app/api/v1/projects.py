"""
Projects API endpoints
Handles project creation, listing, updates, and deletion
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import re
import logging

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListItem
)
from app.services.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_slug(name: str, user_id: int) -> str:
    """Generate URL-friendly slug from project name"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    # Add user_id to ensure uniqueness
    return f"{slug}-{user_id}"


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project
    
    - Creates project with Git repository
    - Associates with current user as owner
    """
    # Generate unique slug
    slug = generate_slug(project_data.name, current_user.id)
    
    # Check if slug already exists
    existing_project = db.query(Project).filter(Project.slug == slug).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    # Create new project
    new_project = Project(
        name=project_data.name,
        slug=slug,
        description=project_data.description,
        visibility=project_data.visibility,
        git_branch=project_data.git_branch,
        owner_id=current_user.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Create default top.v file
    try:
        default_content = """// Top-level module for {project_name}
// Created automatically

module top (
    input wire clk,
    input wire rst_n,
    // Add your ports here
    output wire led
);

    // Your design logic here

endmodule
""".format(project_name=project_data.name)

        # Create file record
        top_file = ProjectFile(
            filename="top.v",
            filepath="src/top.v",
            size_bytes=len(default_content.encode('utf-8')),
            mime_type="text/plain",
            project_id=new_project.id,
            use_minio=True
        )

        db.add(top_file)
        db.commit()
        db.refresh(top_file)

        # Upload content to MinIO
        file_bytes = default_content.encode('utf-8')
        bucket, key, content_hash = storage_service.upload_file(
            file_bytes,
            new_project.id,
            top_file.id,
            "top.v",
            "text/plain"
        )

        # Update file record with MinIO information
        top_file.minio_bucket = bucket
        top_file.minio_key = key
        top_file.content_hash = content_hash
        db.commit()

        logger.info(f"Created default top.v file for project {new_project.id}")
    except Exception as e:
        logger.error(f"Failed to create default top.v file: {e}")
        # Don't fail the project creation if file creation fails

    return new_project


@router.get("/", response_model=List[ProjectListItem])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    visibility: ProjectVisibility = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's projects
    
    - Returns paginated list of projects owned by current user
    - Optionally filter by visibility
    """
    query = db.query(Project).filter(Project.owner_id == current_user.id)
    
    if visibility:
        query = query.filter(Project.visibility == visibility)
    
    projects = query.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    
    return projects


@router.get("/public", response_model=List[ProjectListItem])
async def list_public_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all public projects

    - Returns paginated list of public projects from all users
    - Sorted by popularity (stars_count, then views_count)
    - No authentication required
    """
    projects = (
        db.query(Project)
        .filter(Project.visibility == ProjectVisibility.PUBLIC)
        .order_by(Project.stars_count.desc(), Project.views_count.desc(), Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project details
    
    - Returns full project information
    - User must be owner or project must be public
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access permissions
    if project.owner_id != current_user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project details
    
    - Updates project metadata
    - Only project owner can update
    """
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
            detail="Only project owner can update"
        )
    
    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
        # Regenerate slug if name changes
        project.slug = generate_slug(project_data.name, current_user.id)
    
    if project_data.description is not None:
        project.description = project_data.description
    
    if project_data.visibility is not None:
        project.visibility = project_data.visibility
    
    if project_data.git_branch is not None:
        project.git_branch = project_data.git_branch
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete project
    
    - Permanently deletes project and all associated data
    - Only project owner can delete
    """
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
            detail="Only project owner can delete"
        )
    
    db.delete(project)
    db.commit()
    
    return None
