import uuid
from typing import Optional
from pathlib import Path
from src.services.base import BaseService
from src.storage.base import FileStorage
from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.models.domain import UploadedFile


class FileStorageService(BaseService):
    """Service for file storage operations."""
    
    def __init__(
        self,
        file_storage: FileStorage,
        uploaded_file_repository: Optional[UploadedFileRepository] = None
    ):
        super().__init__()
        self.file_storage = file_storage
        self.uploaded_file_repository = uploaded_file_repository
    
    def generate_key(self, prefix: str = '', original_filename: Optional[str] = None) -> str:
        """
        Generate a unique storage key for a file.
        
        Business rules:
        - Keys are unique and unpredictable (using UUID)
        - Format: uuid/originalname.ext (if original_filename provided)
        - Or: uuid (if no original filename)
        - Prefix is not used in key format (kept for backward compatibility but ignored)
        """
        # Generate unique UUID
        file_uuid = str(uuid.uuid4())
        
        if original_filename:
            # Sanitize filename: remove path components, keep only basename
            path = Path(original_filename)
            safe_filename = path.name  # Get just the filename, no path
            
            key = f'{file_uuid}/{safe_filename}'
        else:
            key = file_uuid
        
        return key

    def prepare_upload_key(self, original_filename: str, custom_key: Optional[str], prefix: str = '') -> tuple[str, str]:
        if custom_key:
            sanitized_key = self._validate_and_sanitize_key(custom_key)
            filename = self.extract_original_filename(sanitized_key)
            return sanitized_key, filename

        generated_key = self.generate_key(prefix=prefix, original_filename=original_filename)
        filename = self.extract_original_filename(generated_key)
        return generated_key, filename
    
    async def store_file(
        self,
        file_data: bytes,
        content_type: Optional[str] = None,
        original_filename: Optional[str] = None,
        custom_key: Optional[str] = None,
        owner_id: Optional[str] = None,
        used_for: Optional[str] = None
    ) -> str:
        """
        Store a file and return its storage key.
        
        Business rules:
        - File data must be provided
        - Key is generated if not provided (format: uuid/filename.ext)
        - Content type is preserved if provided
        - Custom key is validated and sanitized if provided
        - UploadedFile record is created if repository is available and owner_id is provided
        - UUID ensures uniqueness - no overwrites possible
        """
        if not file_data:
            raise ValueError('errors.file.empty')
        
        # Use custom key if provided, otherwise generate one
        if custom_key:
            # Validate and sanitize custom key
            key = self._validate_and_sanitize_key(custom_key)
        else:
            key = self.generate_key(original_filename=original_filename)
        
        # Store the file
        stored_key = await self.file_storage.store(key, file_data, content_type)
        
        # Create UploadedFile record if repository is available and owner_id is provided
        if self.uploaded_file_repository and owner_id:
            try:
                original_name = original_filename or self.extract_original_filename(stored_key)
                uploaded_file = UploadedFile(
                    file_key=stored_key,
                    owner_id=owner_id,
                    original_filename=original_name,
                    content_type=content_type,
                    file_size=len(file_data),
                    used_for=used_for
                )
                await self.uploaded_file_repository.create(uploaded_file)
            except Exception as e:
                self._log_warning(
                    f'Failed to create UploadedFile record: {stored_key}',
                    error=e,
                    owner_id=owner_id
                )
        
        self._log_info(
            f'File stored: {stored_key}',
            key=stored_key,
            content_type=content_type
        )
        
        return stored_key
    
    async def store_file_stream(
        self,
        file_stream,
        content_type: Optional[str] = None,
        original_filename: Optional[str] = None,
        custom_key: Optional[str] = None,
        owner_id: Optional[str] = None,
        used_for: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> tuple[str, int]:
        """
        Store a file from a stream and return its storage key and size.
        
        Business rules:
        - File stream must be provided
        - Key is generated if not provided (format: uuid/filename.ext)
        - Content type is preserved if provided
        - Custom key is validated and sanitized if provided (exactly 2 parts, no nesting)
        - File size is tracked during streaming
        - UploadedFile record is created if repository is available and owner_id is provided
        - UUID ensures uniqueness - no overwrites possible
        """
        # Use custom key if provided, otherwise generate one
        if custom_key:
            # Validate and sanitize custom key
            key = self._validate_and_sanitize_key(custom_key)
        else:
            key = self.generate_key(original_filename=original_filename)
        
        # Track file size during streaming
        file_size = 0
        
        # Create a wrapper to track size and validate during stream
        # FastAPI UploadFile uses .read() method, not async iteration
        async def size_tracking_stream():
            nonlocal file_size
            chunk_size = 8192  # 8KB chunks
            while True:
                chunk = await file_stream.read(chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                if max_size and file_size > max_size:
                    raise ValueError(f'errors.file.size_exceeds:{max_size}')
                yield chunk
        
        # Store the file from stream with size tracking
        stored_key = await self.file_storage.store_stream(key, size_tracking_stream(), content_type)
        
        # Create UploadedFile record if repository is available and owner_id is provided
        if self.uploaded_file_repository and owner_id:
            try:
                original_name = original_filename or self.extract_original_filename(stored_key)
                uploaded_file = UploadedFile(
                    file_key=stored_key,
                    owner_id=owner_id,
                    original_filename=original_name,
                    content_type=content_type,
                    file_size=file_size,
                    used_for=used_for
                    # created_at will be set automatically by repository
                )
                await self.uploaded_file_repository.create(uploaded_file)
            except Exception as e:
                self._log_warning(
                    f'Failed to create UploadedFile record: {stored_key}',
                    error=e,
                    owner_id=owner_id
                )
        
        self._log_info(
            f'File stored from stream: {stored_key}',
            key=stored_key,
            content_type=content_type,
            file_size=file_size
        )
        
        return stored_key, file_size
    
    async def retrieve_file(self, key: str) -> Optional[bytes]:
        """
        Retrieve a file by its storage key.
        
        Business rules:
        - Key must be provided
        - Returns None if file not found
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        file_data = await self.file_storage.retrieve(key)
        return file_data
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete a file by its storage key.
        
        Business rules:
        - Key must be provided
        - Returns True if deleted, False if not found
        - UploadedFile record is deleted if repository is available
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        deleted = await self.file_storage.delete(key)
        
        # Delete UploadedFile record if repository is available
        if deleted and self.uploaded_file_repository:
            try:
                await self.uploaded_file_repository.delete_by_file_key(key)
            except Exception as e:
                self._log_warning(
                    f'Failed to delete UploadedFile record: {key}',
                    error=e
                )
        
        if deleted:
            self._log_info(
                f'File deleted: {key}',
                key=key
            )
        
        return deleted
    
    async def file_exists(self, key: str) -> bool:
        """
        Check if a file exists.
        
        Business rules:
        - Key must be provided
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        return await self.file_storage.exists(key)
    
    def get_file_url(self, key: str) -> str:
        """
        Get URL or path to access a file.
        
        Business rules:
        - Key must be provided
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        return self.file_storage.get_url(key)
    
    def _validate_and_sanitize_key(self, key: str) -> str:
        """
        Validate and sanitize a custom file key.
        
        Business rules:
        - Key must not be empty
        - Key must follow format: prefix/hashkey/originalname.ext (2-3 parts)
        - Key must not contain path traversal sequences
        """
        if not key:
            raise ValueError('errors.file.key_empty')
        
        # Split and validate format
        parts = key.split('/')
        
        # Allow exactly 2 parts: uuid/filename.ext
        if len(parts) != 2:
            raise ValueError('errors.file.invalid_key_format')
        
        # Sanitize each part
        safe_parts = []
        for part in parts:
            # Remove path traversal attempts and separators
            sanitized = part.replace('..', '').replace('/', '').replace('\\', '')
            # Filter out empty parts and dangerous values
            if not sanitized or sanitized in ('', '.', '..'):
                raise ValueError('errors.file.key_invalid_parts')
            safe_parts.append(sanitized)
        
        return '/'.join(safe_parts)
    
    def extract_original_filename(self, key: str) -> str:
        """
        Extract original filename from storage key.
        
        Business rules:
        - Key format: uuid/filename.ext (simple format)
        - Returns the filename part (last segment)
        - Returns key if format doesn't match
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        parts = key.split('/')
        if len(parts) >= 2:
            return parts[-1]
        else:
            return key
    
    async def generate_upload_url(
        self,
        filename: str,
        content_type: Optional[str] = None,
        prefix: str = '',
        expires_in: int = 3600
    ) -> dict:
        """
        Generate upload URL (presigned or regular) for a file.
        
        Business rules:
        - Generates file key upfront (format: uuid/filename.ext)
        - Returns presigned URL for S3, regular upload endpoint for local
        - Returns file_key, upload_url, expires_in, and method
        - Prefix parameter is kept for backward compatibility but ignored
        """
        if not filename:
            raise ValueError('errors.file.filename_required')
        
        file_key = self.generate_key(prefix=prefix, original_filename=filename)
        upload_url = self.file_storage.generate_presigned_upload_url(
            file_key,
            content_type or 'application/octet-stream',
            expires_in
        )
        
        # Local storage returns regular API endpoint (POST method)
        # S3 would return presigned URL (PUT method) - handled by storage implementation
        result = {
            'file_key': file_key,
            'upload_url': upload_url,
            'method': 'POST'
        }
        
        return result
    
    async def get_file_by_key(self, key: str) -> Optional[UploadedFile]:
        """
        Get UploadedFile record by storage key.
        
        Business rules:
        - Key must be provided
        - Returns None if not found or repository not available
        """
        if not key:
            raise ValueError('errors.file.storage_key_required')
        
        if not self.uploaded_file_repository:
            return None
        
        return await self.uploaded_file_repository.get_by_file_key(key)
