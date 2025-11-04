"""
MinIO storage service for project files

Handles file upload, download, and management in MinIO object storage.
"""
import hashlib
import logging
from io import BytesIO
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in MinIO"""

    def __init__(self):
        """Initialize MinIO client"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.files_bucket = settings.MINIO_FILES_BUCKET
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the files bucket exists"""
        try:
            if not self.client.bucket_exists(self.files_bucket):
                self.client.make_bucket(self.files_bucket)
                logger.info(f"Created MinIO bucket: {self.files_bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise

    def generate_file_key(self, project_id: int, file_id: int, filename: str) -> str:
        """
        Generate a unique object key for a file

        Args:
            project_id: Project ID
            file_id: File ID
            filename: Original filename

        Returns:
            Object key in format: projects/{project_id}/files/{file_id}/{filename}
        """
        return f"projects/{project_id}/files/{file_id}/{filename}"

    def upload_file(
        self,
        file_content: bytes,
        project_id: int,
        file_id: int,
        filename: str,
        content_type: str = "text/plain"
    ) -> tuple[str, str, int]:
        """
        Upload a file to MinIO

        Args:
            file_content: File content as bytes
            project_id: Project ID
            file_id: File ID
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            Tuple of (bucket_name, object_key, content_hash)
        """
        try:
            # Generate object key
            object_key = self.generate_file_key(project_id, file_id, filename)

            # Calculate SHA256 hash
            content_hash = hashlib.sha256(file_content).hexdigest()

            # Upload file
            file_stream = BytesIO(file_content)
            self.client.put_object(
                self.files_bucket,
                object_key,
                file_stream,
                length=len(file_content),
                content_type=content_type,
                metadata={"sha256": content_hash}
            )

            logger.info(f"Uploaded file to MinIO: {object_key}")
            return (self.files_bucket, object_key, content_hash)

        except S3Error as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            raise

    def download_file(self, bucket: str, object_key: str) -> bytes:
        """
        Download a file from MinIO

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            File content as bytes
        """
        try:
            response = self.client.get_object(bucket, object_key)
            content = response.read()
            response.close()
            response.release_conn()
            return content

        except S3Error as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            raise

    def delete_file(self, bucket: str, object_key: str):
        """
        Delete a file from MinIO

        Args:
            bucket: Bucket name
            object_key: Object key
        """
        try:
            self.client.remove_object(bucket, object_key)
            logger.info(f"Deleted file from MinIO: {object_key}")

        except S3Error as e:
            logger.error(f"Error deleting file from MinIO: {e}")
            raise

    def file_exists(self, bucket: str, object_key: str) -> bool:
        """
        Check if a file exists in MinIO

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket, object_key)
            return True
        except S3Error:
            return False

    def get_file_metadata(self, bucket: str, object_key: str) -> dict:
        """
        Get file metadata from MinIO

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            Dictionary with metadata (size, content_type, etc.)
        """
        try:
            stat = self.client.stat_object(bucket, object_key)
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "metadata": stat.metadata
            }
        except S3Error as e:
            logger.error(f"Error getting file metadata: {e}")
            raise


# Global storage service instance
storage_service = StorageService()
