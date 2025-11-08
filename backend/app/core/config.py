"""
Core configuration settings for a6hub backend
Uses Pydantic settings management with environment variables
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    PROJECT_NAME: str = "a6hub"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    
    # Database
    POSTGRES_USER: str = "a6hub"
    POSTGRES_PASSWORD: str = "a6hub_dev_password"
    POSTGRES_DB: str = "a6hub"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Alias for DATABASE_URL for SQLAlchemy compatibility"""
        return self.DATABASE_URL
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    # MinIO (S3-compatible storage)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "a6hub-artifacts"  # For job artifacts
    MINIO_FILES_BUCKET: str = "a6hub-files"  # For project files
    MINIO_SECURE: bool = False

    # Yosys configuration for Verilog parsing
    YOSYS_PATH: str = "/usr/bin/yosys"
    
    # Storage paths
    STORAGE_BASE_PATH: str = "/tmp/a6hub-storage"
    GIT_REPOS_PATH: str = "/tmp/a6hub-repos"
    
    # EDA Tools paths (in worker containers)
    LIBRELANE_PATH: str = "/opt/librelane"
    PDK_ROOT: str = "/opt/pdk"
    VERILATOR_PATH: str = "/usr/bin/verilator"
    ICARUS_PATH: str = "/usr/bin/iverilog"
    
    # Job limits
    MAX_JOB_DURATION_SECONDS: int = 3600  # 1 hour
    MAX_PROJECT_SIZE_MB: int = 100
    MAX_FILE_SIZE_MB: int = 10
    
    # Worker configuration
    WORKER_CONTAINER_IMAGE: str = "a6hub-worker:latest"
    WORKER_TIMEOUT: int = 3600
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
