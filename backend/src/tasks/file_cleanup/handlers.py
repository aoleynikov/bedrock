from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from src.models.domain import UploadedFile
from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.repositories.user_repository import UserRepository
from src.services.file_storage_service import FileStorageService
from src.logging.logger import get_logger

logger = get_logger(__name__, 'tasks')


class FileCleanupHandler(ABC):
    """Base handler for file cleanup operations."""
    
    def __init__(
        self,
        uploaded_file_repository: UploadedFileRepository,
        file_storage_service: FileStorageService,
        user_repository: UserRepository = None
    ):
        self.uploaded_file_repository = uploaded_file_repository
        self.file_storage_service = file_storage_service
        self.user_repository = user_repository
    
    @abstractmethod
    def get_file_type(self) -> str:
        """Return the file type this handler processes (e.g., 'avatar', 'document')."""
        pass
    
    @abstractmethod
    async def is_file_used(self, uploaded_file: UploadedFile) -> bool:
        """
        Check if a file is currently in use.
        
        Args:
            uploaded_file: The UploadedFile record to check
        
        Returns:
            True if file is in use, False otherwise
        """
        pass
    
    async def cleanup_files(self, max_age_hours: int = 6, skip: int = 0, limit: int = 1000) -> dict:
        """
        Clean up unused files older than max_age_hours.
        
        Files are considered unused if:
        - They are older than max_age_hours
        - They are not bound to any entity (checked via is_file_used())
        
        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 6)
            skip: Number of files to skip (for pagination)
            limit: Maximum number of files to process
        
        Returns:
            Dictionary with cleanup statistics
        """
        file_type = self.get_file_type()
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Get files of this type older than cutoff (with pagination)
        files = await self.uploaded_file_repository.find_many(
            {
                'used_for': file_type,
                'created_at': {'$lt': cutoff_time}
            },
            skip=skip,
            limit=limit
        )
        
        deleted_count = 0
        failed_count = 0
        skipped_count = 0
        
        for uploaded_file in files:
            try:
                # Check if file is still in use
                if await self.is_file_used(uploaded_file):
                    skipped_count += 1
                    continue
                
                # Delete file from storage (service handles both storage and DB record deletion)
                deleted = await self.file_storage_service.delete_file(uploaded_file.file_key)
                
                if deleted:
                    deleted_count += 1
                    age_hours = None
                    if uploaded_file.created_at:
                        age_hours = (datetime.utcnow() - uploaded_file.created_at).total_seconds() / 3600
                    logger.info(
                        f'Cleaned up unused {file_type} file: {uploaded_file.file_key}',
                        extra={
                            'file_key': uploaded_file.file_key,
                            'file_type': file_type,
                            'age_hours': age_hours
                        }
                    )
                else:
                    failed_count += 1
                    logger.warning(
                        f'Failed to delete file from storage: {uploaded_file.file_key}',
                        extra={'file_key': uploaded_file.file_key, 'file_type': file_type}
                    )
            except Exception as e:
                failed_count += 1
                logger.error(
                    f'Error cleaning up file: {uploaded_file.file_key}',
                    error=e,
                    extra={'file_key': uploaded_file.file_key, 'file_type': file_type}
                )
        
        return {
            'file_type': file_type,
            'processed': len(files),
            'deleted': deleted_count,
            'skipped': skipped_count,
            'failed': failed_count
        }


class AvatarFileCleanupHandler(FileCleanupHandler):
    """Handler for cleaning up avatar files."""
    
    def get_file_type(self) -> str:
        return 'avatar'
    
    async def is_file_used(self, uploaded_file: UploadedFile) -> bool:
        """
        Check if avatar file is in use by checking if any user has it as their avatar.
        """
        if not self.user_repository:
            return False
        
        # Check if any user has this file_key as their avatar
        user = await self.user_repository.find_one({'avatar_file_key': uploaded_file.file_key})
        return user is not None


class DocumentFileCleanupHandler(FileCleanupHandler):
    """Handler for cleaning up document files."""
    
    def get_file_type(self) -> str:
        return 'document'
    
    async def is_file_used(self, uploaded_file: UploadedFile) -> bool:
        """
        Check if document file is in use.
        
        For now, documents are considered unused if they're older than the cleanup window.
        In the future, this could check if document is referenced in other entities.
        """
        return False


class DefaultFileCleanupHandler(FileCleanupHandler):
    """Default handler for files without a specific type or unknown types."""
    
    def get_file_type(self) -> str:
        return 'untyped'
    
    async def is_file_used(self, uploaded_file: UploadedFile) -> bool:
        """
        Default behavior: files without a type are considered unused if older than the cleanup window.
        """
        return False
    
    async def cleanup_files(self, max_age_hours: int = 6, skip: int = 0, limit: int = 1000) -> dict:
        """
        Clean up files without a used_for type.
        
        These are files that were uploaded but never bound to any entity.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 6)
            skip: Number of files to skip (for pagination)
            limit: Maximum number of files to process
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Get files without used_for or with null used_for, older than cutoff (with pagination)
        files = await self.uploaded_file_repository.find_many(
            {
                '$or': [
                    {'used_for': None},
                    {'used_for': {'$exists': False}}
                ],
                'created_at': {'$lt': cutoff_time}
            },
            skip=skip,
            limit=limit
        )
        
        deleted_count = 0
        failed_count = 0
        
        for uploaded_file in files:
            try:
                # Delete file from storage (service handles both storage and DB record deletion)
                deleted = await self.file_storage_service.delete_file(uploaded_file.file_key)
                
                if deleted:
                    deleted_count += 1
                    logger.info(
                        f'Cleaned up unused file without type: {uploaded_file.file_key}',
                        extra={'file_key': uploaded_file.file_key}
                    )
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(
                    f'Error cleaning up file: {uploaded_file.file_key}',
                    error=e,
                    extra={'file_key': uploaded_file.file_key}
                )
        
        return {
            'file_type': 'untyped',
            'processed': len(files),
            'deleted': deleted_count,
            'skipped': 0,
            'failed': failed_count
        }
