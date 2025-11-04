"""
Project Files API endpoints
Handles file uploads, downloads, and management within projects
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.security import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.schemas.project import (
    ProjectFileCreate,
    ProjectFileUpdate,
    ProjectFileResponse,
    ProjectFileWithContent
)
from app.services.module_extractor import module_extractor

logger = logging.getLogger(__name__)

router = APIRouter()


def check_project_access(project: Project, user: User, write_access: bool = False):
    """
    Check if user has access to project
    
    Args:
        project: Project to check
        user: Current user
        write_access: If True, requires ownership
    
    Raises:
        HTTPException: If access denied
    """
    if write_access:
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can modify files"
            )
    else:
        if project.owner_id != user.id and project.visibility != ProjectVisibility.PUBLIC:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )


@router.get("/{project_id}/files", response_model=List[ProjectFileResponse])
async def list_project_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files in a project
    
    - Returns list of files with metadata
    - User must have read access to project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user)
    
    files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    
    return files


@router.post("/{project_id}/files", response_model=ProjectFileResponse, status_code=status.HTTP_201_CREATED)
async def create_project_file(
    project_id: int,
    file_data: ProjectFileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new file in project
    
    - Adds new file with content
    - Only project owner can create files
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user, write_access=True)
    
    # Check if file already exists
    existing_file = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.filepath == file_data.filepath
    ).first()
    
    if existing_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File already exists at this path"
        )
    
    # Calculate file size
    size_bytes = len(file_data.content.encode('utf-8')) if file_data.content else 0
    
    # Check file size limit
    if size_bytes > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)"
        )
    
    # Create new file
    new_file = ProjectFile(
        filename=file_data.filename,
        filepath=file_data.filepath,
        content=file_data.content,
        size_bytes=size_bytes,
        mime_type=file_data.mime_type,
        project_id=project_id,
        use_minio=False  # Using legacy content storage for now
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # Extract modules from file content
    if file_data.content:
        try:
            result = module_extractor.extract_modules_from_file(
                file_data.content,
                new_file.id,
                project_id,
                file_data.filename,
                db
            )
            logger.info(f"Extracted {result.modules_found} modules from {file_data.filename}")
        except Exception as e:
            logger.error(f"Error extracting modules from {file_data.filename}: {e}")
            # Don't fail the file creation if module extraction fails

    return new_file


@router.get("/{project_id}/files/{file_id}", response_model=ProjectFileWithContent)
async def get_project_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get file content
    
    - Returns file with full content
    - User must have read access to project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user)
    
    file = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return file


@router.put("/{project_id}/files/{file_id}", response_model=ProjectFileResponse)
async def update_project_file(
    project_id: int,
    file_id: int,
    file_data: ProjectFileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update file content
    
    - Updates file content and/or filename
    - Only project owner can update files
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user, write_access=True)
    
    file = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Update content if provided
    content_updated = False
    if file_data.content is not None:
        file.content = file_data.content
        file.size_bytes = len(file_data.content.encode('utf-8'))
        content_updated = True

        # Check file size limit
        if file.size_bytes > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)"
            )

    # Update filename if provided
    if file_data.filename is not None:
        file.filename = file_data.filename

    db.commit()
    db.refresh(file)

    # Re-extract modules if content was updated
    if content_updated and file.content:
        try:
            result = module_extractor.extract_modules_from_file(
                file.content,
                file.id,
                project_id,
                file.filename,
                db
            )
            logger.info(f"Re-extracted {result.modules_found} modules from {file.filename}")
        except Exception as e:
            logger.error(f"Error re-extracting modules from {file.filename}: {e}")
            # Don't fail the file update if module extraction fails

    return file


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete file
    
    - Permanently removes file from project
    - Only project owner can delete files
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    check_project_access(project, current_user, write_access=True)
    
    file = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    db.delete(file)
    db.commit()
    
    return None
