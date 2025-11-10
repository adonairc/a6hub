"""
KWeb GDS Viewer API endpoints
Serves GDS files through KLayout web viewer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
import os
import tempfile
import logging

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.services.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


def check_project_access(project: Project, user: User):
    """Check if user has access to project"""
    if project.owner_id != user.id and project.visibility != ProjectVisibility.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.get("/gds/{project_id}/{filename}")
async def view_gds_file(
    project_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serve GDS file through KLayout web viewer

    This endpoint returns an HTML page that embeds the KLayout viewer
    for the specified GDS file.
    """
    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, current_user)

    # Find the GDS file
    gds_file = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.filename == filename
    ).first()

    if not gds_file:
        # Return a helpful message if file doesn't exist
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GDS Not Found</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .message {{
                    background: white;
                    padding: 2rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }}
                .icon {{
                    font-size: 64px;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    margin: 0 0 1rem 0;
                    color: #333;
                }}
                p {{
                    color: #666;
                    line-height: 1.5;
                }}
                .filename {{
                    font-family: monospace;
                    background: #f3f4f6;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="message">
                <div class="icon">📁</div>
                <h1>GDS File Not Found</h1>
                <p>The file <span class="filename">{filename}</span> doesn't exist yet.</p>
                <p>Run your Python gdsfactory script to generate the GDS file, then refresh this viewer.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # For now, return a placeholder viewer
    # TODO: Integrate actual kweb viewer
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KLayout GDS Viewer - {filename}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                background: #1a1a1a;
                color: white;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }}
            .header {{
                background: #2d2d2d;
                padding: 1rem;
                border-bottom: 1px solid #444;
            }}
            .viewer {{
                flex: 1;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                gap: 1rem;
            }}
            .status {{
                background: #2d2d2d;
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
            }}
            .icon {{
                font-size: 48px;
                margin-bottom: 1rem;
            }}
            .filename {{
                font-family: monospace;
                background: #3d3d3d;
                padding: 0.5rem 1rem;
                border-radius: 4px;
            }}
            .info {{
                color: #888;
                font-size: 14px;
                max-width: 600px;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0;">KLayout GDS Viewer</h2>
        </div>
        <div class="viewer">
            <div class="status">
                <div class="icon">🔧</div>
                <h3>Viewer Integration In Progress</h3>
                <p class="filename">{filename}</p>
                <p class="info">
                    The KLayout web viewer (kweb) integration is being configured.
                    This will display the GDS layout generated from your Python gdsfactory script.
                </p>
                <p class="info">
                    <strong>Next steps:</strong><br>
                    1. Install kweb: <code>pip install kweb</code><br>
                    2. Configure the kweb service in the backend<br>
                    3. The viewer will automatically display your GDS files here
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/download/{project_id}/{filename}")
async def download_gds_file(
    project_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download GDS file directly
    """
    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, current_user)

    # Find the GDS file
    gds_file = db.query(ProjectFile).filter(
        ProjectFile.project_id == project_id,
        ProjectFile.filename == filename
    ).first()

    if not gds_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GDS file not found"
        )

    # Download from MinIO
    if gds_file.minio_bucket and gds_file.minio_key:
        try:
            file_bytes = storage_service.download_file(gds_file.minio_bucket, gds_file.minio_key)

            # Write to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.gds')
            temp_file.write(file_bytes)
            temp_file.close()

            return FileResponse(
                temp_file.name,
                media_type="application/octet-stream",
                filename=filename
            )
        except Exception as e:
            logger.error(f"Error downloading GDS file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download GDS file"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage"
        )
