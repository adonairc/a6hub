"""
Import all models here to ensure they are registered with SQLAlchemy
"""
from app.models.user import User
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.job import Job, JobType, JobStatus
from app.models.forum import ForumCategory, ForumTopic, ForumPost
from app.models.module import Module, ModuleType

__all__ = [
    "User",
    "Project",
    "ProjectVisibility",
    "ProjectFile",
    "Job",
    "JobType",
    "JobStatus",
    "ForumCategory",
    "ForumTopic",
    "ForumPost",
    "Module",
    "ModuleType",
]
