"""
Modules API endpoints

Handles CRUD operations for design modules extracted from files.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.module import Module, ModuleType
from app.models.project_file import ProjectFile
from app.schemas.module import (
    ModuleResponse,
    ModuleListItem,
    ModuleWithFile,
    ModuleParseResult,
    ModuleUpdate
)
from app.services.module_extractor import module_extractor

router = APIRouter()


def check_project_access(project: Project, user: User):
    """Check if user has access to project"""
    if project.owner_id != user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.get("/{project_id}/modules", response_model=List[ModuleWithFile])
async def list_project_modules(
    project_id: int,
    module_type: Optional[ModuleType] = None,
    search: Optional[str] = Query(None, description="Search by module name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all modules in a project

    - Filter by module type (verilog_module, python_class, etc.)
    - Search by module name
    - Returns modules with file information
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, current_user)

    # Build query
    query = db.query(Module).filter(Module.project_id == project_id)

    if module_type:
        query = query.filter(Module.module_type == module_type)

    if search:
        query = query.filter(Module.name.ilike(f"%{search}%"))

    modules = query.order_by(Module.name).all()

    # Add file information
    result = []
    for module in modules:
        module_dict = {
            **module.__dict__,
            "filename": module.file.filename if module.file else "unknown",
            "filepath": module.file.filepath if module.file else ""
        }
        result.append(ModuleWithFile.model_validate(module_dict))

    return result


@router.get("/{project_id}/modules/{module_id}", response_model=ModuleResponse)
async def get_module(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get module details

    - Returns full module information including metadata
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, current_user)

    module = db.query(Module).filter(
        Module.id == module_id,
        Module.project_id == project_id
    ).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    return module


@router.put("/{project_id}/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    project_id: int,
    module_id: int,
    module_update: ModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update module information

    - Only owner can update modules
    - Can update name, description, metadata
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Only owner can update
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can update modules"
        )

    module = db.query(Module).filter(
        Module.id == module_id,
        Module.project_id == project_id
    ).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # Update fields
    if module_update.name is not None:
        module.name = module_update.name

    if module_update.description is not None:
        module.description = module_update.description

    if module_update.module_metadata is not None:
        module.module_metadata = module_update.module_metadata

    db.commit()
    db.refresh(module)

    return module


@router.delete("/{project_id}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    project_id: int,
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a module

    - Only owner can delete modules
    - Note: Modules are usually auto-regenerated when file is saved
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Only owner can delete
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete modules"
        )

    module = db.query(Module).filter(
        Module.id == module_id,
        Module.project_id == project_id
    ).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    db.delete(module)
    db.commit()

    return None


@router.post("/{project_id}/modules/reparse", response_model=ModuleParseResult)
async def reparse_project_modules(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Re-parse all files in a project to extract modules

    - Useful after updating parser or for bulk operations
    - Deletes existing modules and re-extracts from source files
    - Only owner can trigger re-parsing
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Only owner can reparse
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can reparse modules"
        )

    # Re-extract all modules
    result = module_extractor.re_extract_all_modules(project_id, db)

    return result


@router.post("/{project_id}/files/{file_id}/parse", response_model=ModuleParseResult)
async def parse_file_modules(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a specific file to extract modules

    - Useful for re-parsing a single file after editing
    - Deletes existing modules for this file and re-extracts
    - Only owner can trigger parsing
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Only owner can parse
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can parse files"
        )

    file = db.query(ProjectFile).filter(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id
    ).first()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Get file content
    file_content = None
    if file.use_minio and file.minio_bucket and file.minio_key:
        # TODO: Download from MinIO
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MinIO download not yet implemented"
        )
    elif file.content:
        file_content = file.content
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no content"
        )

    # Extract modules
    result = module_extractor.extract_modules_from_file(
        file_content,
        file.id,
        project_id,
        file.filename,
        db
    )

    return result
