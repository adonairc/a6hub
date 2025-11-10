"""
KWeb GDS Viewer Service
Manages GDS file serving through KLayout web viewer
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional
import shutil

logger = logging.getLogger(__name__)


class KWebService:
    """Service for managing KLayout web viewer integration"""

    def __init__(self):
        """Initialize KWeb service with temporary directory for GDS files"""
        # Create a temporary directory for GDS files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kweb_gds_"))
        logger.info(f"Initialized KWeb service with temp directory: {self.temp_dir}")

    def save_gds_file(self, file_bytes: bytes, project_id: int, filename: str) -> str:
        """
        Save GDS file to temporary directory for kweb access

        Args:
            file_bytes: GDS file content as bytes
            project_id: Project ID
            filename: GDS filename

        Returns:
            Path to saved GDS file
        """
        # Create project-specific subdirectory
        project_dir = self.temp_dir / str(project_id)
        project_dir.mkdir(exist_ok=True)

        # Save file
        file_path = project_dir / filename
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        logger.info(f"Saved GDS file to {file_path}")
        return str(file_path)

    def get_gds_path(self, project_id: int, filename: str) -> Optional[str]:
        """
        Get path to GDS file if it exists

        Args:
            project_id: Project ID
            filename: GDS filename

        Returns:
            Path to GDS file or None if not found
        """
        file_path = self.temp_dir / str(project_id) / filename
        if file_path.exists():
            return str(file_path)
        return None

    def cleanup_project_files(self, project_id: int):
        """
        Clean up all GDS files for a project

        Args:
            project_id: Project ID
        """
        project_dir = self.temp_dir / str(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir)
            logger.info(f"Cleaned up GDS files for project {project_id}")

    def cleanup(self):
        """Clean up all temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up KWeb temp directory: {self.temp_dir}")

    def get_project_dir(self, project_id: int) -> str:
        """
        Get the directory path for a project's GDS files

        Args:
            project_id: Project ID

        Returns:
            Path to project directory
        """
        project_dir = self.temp_dir / str(project_id)
        project_dir.mkdir(exist_ok=True)
        return str(project_dir)


# Global instance
kweb_service = KWebService()
