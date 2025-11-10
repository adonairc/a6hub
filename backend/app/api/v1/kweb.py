"""
KWeb GDS Viewer API endpoints
Serves GDS files through KLayout web viewer
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse, FileResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
import os
import tempfile
import logging
from pathlib import Path
import httpx

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.services.storage import storage_service
from app.services.kweb_service import kweb_service

# For token-based auth in iframes
from jose import JWTError, jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Try to import kweb to check availability
KWEB_AVAILABLE = False

try:
    from kweb.viewer import get_app as get_kweb_app
    KWEB_AVAILABLE = True
    logger.info(f"KWeb viewer module is available")
except ImportError as e:
    KWEB_AVAILABLE = False
    logger.warning(f"KWeb is not installed. GDS viewer will show placeholder. Error: {e}")
except Exception as e:
    KWEB_AVAILABLE = False
    logger.error(f"Failed to import KWeb: {e}")


async def call_kweb_internal(path: str) -> Optional[httpx.Response]:
    """
    Make async internal request to mounted kweb app

    Args:
        path: Path to request from kweb (e.g., "/gds/file.gds")

    Returns:
        httpx.Response or None if failed
    """
    if not KWEB_AVAILABLE:
        return None

    try:
        # Use httpx to make async request to the mounted kweb app
        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get(f"/kweb-internal{path}")
            return response
    except Exception as e:
        logger.error(f"Failed to call kweb internal: {e}")
        return None


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """Get user from JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except (JWTError, ValueError):
        return None


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
    request: Request,
    token: str = Query(..., description="Authentication token"),
    db: Session = Depends(get_db)
):
    """
    Serve GDS file through KLayout web viewer

    This endpoint returns an HTML page that embeds the KLayout viewer
    for the specified GDS file.

    Requires token parameter for authentication (used in iframes).
    """
    # Get user from token
    user = get_user_from_token(token, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )

    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, user)

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

    # Download GDS file from MinIO and save to kweb temp directory
    if gds_file.minio_bucket and gds_file.minio_key:
        try:
            # Download from MinIO
            file_bytes = storage_service.download_file(gds_file.minio_bucket, gds_file.minio_key)

            # Save to kweb service temp directory
            file_path = kweb_service.save_gds_file(file_bytes, project_id, filename)

            logger.info(f"Prepared GDS file for viewing: {file_path}")

            # If kweb is available, return HTML that iframes the viewer
            if KWEB_AVAILABLE:
                viewer_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>KLayout GDS Viewer - {filename}</title>
                    <meta charset="utf-8">
                    <style>
                        body, html {{
                            margin: 0;
                            padding: 0;
                            height: 100%;
                            overflow: hidden;
                        }}
                        iframe {{
                            width: 100%;
                            height: 100%;
                            border: none;
                        }}
                    </style>
                </head>
                <body>
                    <iframe src="/api/v1/kweb/viewer/{project_id}/{filename}?token={token}" title="KLayout GDS Viewer"></iframe>
                </body>
                </html>
                """
                return HTMLResponse(content=viewer_html)

        except Exception as e:
            logger.error(f"Error preparing GDS file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load GDS file"
            )

    # Fallback: Show installation instructions
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
                padding: 2rem;
                border-radius: 8px;
                text-align: center;
                max-width: 600px;
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
                display: inline-block;
                margin: 1rem 0;
            }}
            .info {{
                color: #aaa;
                font-size: 14px;
                line-height: 1.6;
                text-align: left;
            }}
            code {{
                background: #3d3d3d;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-family: monospace;
                color: #4ade80;
            }}
            .success {{
                color: #4ade80;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2 style="margin: 0;">KLayout GDS Viewer</h2>
        </div>
        <div class="viewer">
            <div class="status">
                <div class="icon">✅</div>
                <h3 class="success">GDS File Ready</h3>
                <p class="filename">{filename}</p>
                <div class="info">
                    <p><strong>Status:</strong> GDS file is available for viewing</p>
                    <p><strong>To enable the KLayout viewer:</strong></p>
                    <ol style="text-align: left;">
                        <li>Install kweb in the backend: <code>pip install kweb</code></li>
                        <li>Restart the backend server</li>
                        <li>The interactive KLayout viewer will automatically load here</li>
                    </ol>
                    <p style="margin-top: 1.5rem;">
                        <a href="/api/v1/kweb/download/{project_id}/{filename}?token={token}"
                           style="color: #60a5fa; text-decoration: none;">
                            📥 Download GDS file
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/viewer/{project_id}/{filename}")
async def kweb_viewer_direct(
    request: Request,
    project_id: int,
    filename: str,
    token: str = Query(..., description="Authentication token"),
    db: Session = Depends(get_db)
):
    """
    Direct kweb viewer endpoint - serves the actual KLayout viewer interface

    Requires token parameter for authentication (used in iframes).
    """
    if not KWEB_AVAILABLE:
        return HTMLResponse(
            content="<html><body><h1>KWeb not installed</h1><p>Install kweb with: pip install kweb</p><p>Then rebuild the Docker container.</p></body></html>"
        )

    # Get user from token
    user = get_user_from_token(token, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )

    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    check_project_access(project, user)

    # Ensure GDS file exists in temp directory
    gds_path = kweb_service.get_gds_path(project_id, filename)
    if not gds_path:
        # Try to download from MinIO
        gds_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.filename == filename
        ).first()

        if gds_file and gds_file.minio_bucket and gds_file.minio_key:
            file_bytes = storage_service.download_file(gds_file.minio_bucket, gds_file.minio_key)
            gds_path = kweb_service.save_gds_file(file_bytes, project_id, filename)
        else:
            return HTMLResponse(
                content="<html><body><h1>GDS file not found</h1></body></html>"
            )

    # Verify file exists before calling kweb
    actual_file_path = Path(gds_path)
    if not actual_file_path.exists():
        logger.error(f"GDS file does not exist at expected path: {gds_path}")
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>GDS file not found at path: {gds_path}</p></body></html>"
        )

    # Get the flattened filename that kweb will use
    kweb_filename = kweb_service.get_kweb_filename(project_id, filename)

    logger.info(f"GDS file verified at: {gds_path}")
    logger.info(f"KWeb temp_dir: {kweb_service.temp_dir}")
    logger.info(f"Requesting kweb with flat filename: /gds/{kweb_filename}")

    # List all files in temp_dir for debugging
    temp_dir_files = list(Path(kweb_service.temp_dir).iterdir())
    logger.info(f"Files currently in temp_dir: {temp_dir_files}")
    logger.info(f"Target file exists: {Path(gds_path).exists()}")
    logger.info(f"Target file size: {Path(gds_path).stat().st_size if Path(gds_path).exists() else 'N/A'}")

    # Call kweb mounted app internally
    # KWeb expects: /gds/<filename>
    # Files are stored with flat naming: project_{id}_{filename}
    try:
        kweb_response = await call_kweb_internal(f"/gds/{kweb_filename}")

        if kweb_response and kweb_response.status_code == 200:
            logger.info(f"KWeb response status: {kweb_response.status_code}")
            return HTMLResponse(
                content=kweb_response.text,
                status_code=kweb_response.status_code,
                headers=dict(kweb_response.headers)
            )
        else:
            if kweb_response:
                logger.warning(f"KWeb returned status {kweb_response.status_code}")
                logger.error(f"KWeb response body: {kweb_response.text[:500]}")
            else:
                logger.error("Failed to get response from kweb")

    except Exception as e:
        logger.error(f"Error calling kweb: {e}", exc_info=True)

    # Fallback to error viewer
    html = f"""
    <!DOCTYPE html>
        <html>
        <head>
            <title>KLayout Viewer - {filename}</title>
            <meta charset="utf-8">
            <style>
                body, html {{
                    margin: 0;
                    padding: 0;
                    height: 100%;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #1a1a1a;
                    color: white;
                }}
                .container {{
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }}
                .toolbar {{
                    background: #2c2c2c;
                    padding: 10px 20px;
                    display: flex;
                    align-items: center;
                    gap: 20px;
                    border-bottom: 1px solid #444;
                }}
                .viewer {{
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .placeholder {{
                    text-align: center;
                    max-width: 600px;
                    padding: 2rem;
                }}
                .status {{
                    background: #4CAF50;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                }}
                .error {{
                    background: #f44336;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    font-family: monospace;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="toolbar">
                    <strong>KLayout GDS Viewer</strong>
                    <span class="status">● File Ready</span>
                    <span style="margin-left: auto; font-family: monospace;">{filename}</span>
                </div>
                <div class="viewer">
                    <div class="placeholder">
                        <h2>🔬 GDS File Ready</h2>
                        <p>File: <strong>{filename}</strong></p>
                        <div class="error">
                            Error loading kweb viewer. File exists but viewer failed to load.
                        </div>
                        <p style="color: #aaa; margin-top: 2rem;">
                            The GDS file is available and ready for viewing.<br>
                            Make sure kweb is properly installed and the Docker container is rebuilt.
                        </p>
                        <p style="margin-top: 30px;">
                            <a href="/api/v1/kweb/download/{project_id}/{filename}?token={token}"
                               style="background: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
                                📥 Download GDS File
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    return HTMLResponse(content=html)


@router.get("/debug/list-files")
async def debug_list_kweb_files():
    """Debug endpoint to see what files kweb can access"""
    if not KWEB_AVAILABLE:
        return {"error": "KWeb not available"}

    try:
        # Call kweb root
        response = await call_kweb_internal("/")

        # List files in temp_dir
        temp_dir_files = [str(f) for f in Path(kweb_service.temp_dir).iterdir()]

        result = {
            "kweb_available": KWEB_AVAILABLE,
            "temp_dir": str(kweb_service.temp_dir),
            "files_in_temp_dir": temp_dir_files,
        }

        if response:
            result["kweb_root_status"] = response.status_code
            result["kweb_root_response"] = response.text[:500] if response.status_code == 200 else response.text
        else:
            result["kweb_root_status"] = "No response"

        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/assets/{path:path}")
async def serve_kweb_assets(path: str):
    """
    Serve static assets from kweb (JS, CSS, fonts, etc.)

    No authentication needed for static assets.
    """
    if not KWEB_AVAILABLE:
        raise HTTPException(status_code=404, detail="KWeb not available")

    try:
        # Call kweb for asset
        kweb_response = await call_kweb_internal(f"/{path}")

        if kweb_response and kweb_response.status_code == 200:
            # Determine content type based on file extension
            content_type = kweb_response.headers.get("content-type", "application/octet-stream")

            return Response(
                content=kweb_response.content,
                media_type=content_type,
                headers=dict(kweb_response.headers)
            )
        elif kweb_response:
            raise HTTPException(status_code=kweb_response.status_code, detail="Asset not found")
        else:
            raise HTTPException(status_code=500, detail="Failed to contact kweb")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving kweb asset {path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load asset")


@router.get("/download/{project_id}/{filename}")
async def download_gds_file(
    project_id: int,
    filename: str,
    token: str = Query(..., description="Authentication token"),
    db: Session = Depends(get_db)
):
    """
    Download GDS file directly

    Requires token parameter for authentication.
    """
    # Get user from token
    user = get_user_from_token(token, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )

    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    check_project_access(project, user)

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
