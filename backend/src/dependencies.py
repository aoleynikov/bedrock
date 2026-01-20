"""
Dependency injection for services and repositories.
"""
from fastapi import Depends
from src.config import settings
from src.repositories import get_user_repository, get_uploaded_file_repository
from src.repositories.user_repository import UserRepository
from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.services.user_service import UserService
from src.services.task_service import TaskService
from src.services.health_service import HealthService
from src.services.file_storage_service import FileStorageService
from src.storage.local_file_store import LocalFileStore
from src.storage.s3_file_store import S3FileStore
from src.storage.base import FileStorage


def get_file_storage() -> FileStorage:
    """Dependency injection for FileStorage based on configuration."""
    if settings.file_storage_type == 's3':
        if not settings.s3_bucket_name:
            raise ValueError('errors.storage.s3_bucket_required')
        return S3FileStore(
            bucket_name=settings.s3_bucket_name,
            region=settings.s3_region
        )
    else:
        return LocalFileStore(base_path=settings.file_storage_path)


def get_file_storage_service(
    file_storage: FileStorage = Depends(get_file_storage),
    uploaded_file_repository: UploadedFileRepository = Depends(get_uploaded_file_repository)
) -> FileStorageService:
    """Dependency injection for FileStorageService."""
    return FileStorageService(file_storage, uploaded_file_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    file_storage_service: FileStorageService = Depends(get_file_storage_service)
) -> UserService:
    """Dependency injection for UserService."""
    return UserService(user_repository, file_storage_service)


def get_task_service() -> TaskService:
    """Dependency injection for TaskService."""
    return TaskService()


def get_health_service() -> HealthService:
    """Dependency injection for HealthService."""
    return HealthService()
