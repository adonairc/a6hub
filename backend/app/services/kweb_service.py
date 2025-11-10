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

from app.core.config import settings

logger = logging.getLogger(__name__)


class KWebService:
    """Service for managing KLayout web viewer integration"""

    def __init__(self):
        """Initialize KWeb service with persistent directory for GDS files"""
        # Use persistent directory instead of temp directory
        # This ensures files persist across app restarts and kweb can see them
        storage_base = Path(settings.STORAGE_BASE_PATH)
        self.temp_dir = storage_base / "kweb_gds"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized KWeb service with persistent directory: {self.temp_dir}")

        # Create a README file so the directory isn't empty at mount time
        readme_path = self.temp_dir / "README.txt"
        if not readme_path.exists():
            readme_path.write_text(
                "GDS files for KLayout web viewer\n"
                "Files are named: project_{id}_{filename}.gds\n"
                "This directory is persistent and shared with kweb viewer.\n"
            )
            logger.info("Created README in kweb directory")

    def _get_flat_filename(self, project_id: int, filename: str) -> str:
        """
        Generate a flat filename that includes project_id to avoid conflicts

        Args:
            project_id: Project ID
            filename: Original GDS filename

        Returns:
            Flattened filename like "project_1_inverter.gds"
        """
        return f"project_{project_id}_{filename}"

    def save_gds_file(self, file_bytes: bytes, project_id: int, filename: str) -> str:
        """
        Save GDS file to temporary directory for kweb access

        Files are saved with flat naming scheme (project_{id}_{filename})
        to ensure kweb compatibility.

        Args:
            file_bytes: GDS file content as bytes
            project_id: Project ID
            filename: GDS filename

        Returns:
            Path to saved GDS file
        """
        # Use flat naming scheme for kweb compatibility
        flat_filename = self._get_flat_filename(project_id, filename)
        file_path = self.temp_dir / flat_filename

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
        flat_filename = self._get_flat_filename(project_id, filename)
        file_path = self.temp_dir / flat_filename
        if file_path.exists():
            return str(file_path)
        return None

    def get_kweb_filename(self, project_id: int, filename: str) -> str:
        """
        Get the filename that kweb should use to access this file

        Args:
            project_id: Project ID
            filename: Original GDS filename

        Returns:
            Flat filename for kweb access
        """
        return self._get_flat_filename(project_id, filename)

    def cleanup_project_files(self, project_id: int):
        """
        Clean up all GDS files for a project

        Args:
            project_id: Project ID
        """
        # Find and remove all files matching project_{project_id}_*
        pattern = f"project_{project_id}_*"
        for file_path in self.temp_dir.glob(pattern):
            if file_path.is_file():
                file_path.unlink()
                logger.info(f"Deleted GDS file: {file_path}")

        logger.info(f"Cleaned up GDS files for project {project_id}")

    def cleanup(self):
        """Clean up all temporary files"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up KWeb temp directory: {self.temp_dir}")


# Global instance
kweb_service = KWebService()
