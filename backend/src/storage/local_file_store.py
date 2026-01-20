from pathlib import Path
from typing import Optional
from urllib.parse import quote
from src.storage.base import FileStorage
from src.logging.logger import get_logger


class LocalFileStore(FileStorage):
    """Local file storage implementation using mounted volumes."""
    
    def __init__(self, base_path: str = 'storage/uploads'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)
    
    def _get_file_path(self, key: str) -> Path:
        """Get the full file path for a given key."""
        # Robust path traversal protection
        parts = key.split('/')
        safe_parts = []
        for part in parts:
            # Remove all path traversal attempts and separators
            part = part.replace('..', '').replace('/', '').replace('\\', '')
            # Filter out empty parts and dangerous values
            if part and part not in ('', '.', '..'):
                safe_parts.append(part)
        return self.base_path / Path(*safe_parts)
    
    async def store(self, key: str, file_data: bytes, content_type: Optional[str] = None) -> str:
        """
        Store a file locally.
        
        Args:
            key: Unique identifier for the file
            file_data: File content as bytes
            content_type: MIME type (not used in local storage, but kept for interface consistency)
        
        Returns:
            The storage key
        """
        file_path = self._get_file_path(key)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        self.logger.info(
            f'File stored: {key}',
            extra={'key': key, 'path': str(file_path)}
        )
        
        return key
    
    async def store_stream(self, key: str, file_stream, content_type: Optional[str] = None) -> str:
        """
        Store a file from a stream locally.
        
        Args:
            key: Unique identifier for the file (format: uuid/filename.ext, exactly 2 parts)
            file_stream: File content as an async iterator or file-like object (FastAPI UploadFile)
            content_type: MIME type (not used in local storage, but kept for interface consistency)
        
        Returns:
            The storage key
        """
        file_path = self._get_file_path(key)
        
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file from stream
        # FastAPI UploadFile supports async iteration
        with open(file_path, 'wb') as f:
            async for chunk in file_stream:
                f.write(chunk)
        
        self.logger.info(
            f'File stored from stream: {key}',
            extra={'key': key, 'path': str(file_path)}
        )
        
        return key
    
    async def retrieve(self, key: str) -> Optional[bytes]:
        """
        Retrieve a file from local storage.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            File content as bytes, or None if not found
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            self.logger.error(
                f'Error retrieving file: {key}',
                error=e,
                extra={'key': key}
            )
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a file from local storage.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            True if deleted, False if not found
        """
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            self.logger.info(
                f'File deleted: {key}',
                extra={'key': key}
            )
            return True
        except Exception as e:
            self.logger.error(
                f'Error deleting file: {key}',
                error=e,
                extra={'key': key}
            )
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in local storage.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            True if file exists, False otherwise
        """
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    def get_url(self, key: str) -> str:
        """
        Get the file path for local storage.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            URL path to the file (served via FastAPI static files)
        """
        # Return URL path that will be served by FastAPI StaticFiles
        return f'/storage/{key}'
    
    def generate_presigned_upload_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        """
        Generate upload URL for local storage.
        
        For local storage, this returns the regular upload endpoint with the file_key parameter.
        Note: Local storage doesn't have true presigned URLs (that's an S3 concept), so this
        returns the standard upload endpoint that accepts the pre-generated file_key.
        
        Args:
            key: Unique identifier for the file
            content_type: MIME type (not used for local, but kept for interface consistency)
            expires_in: Expiration time (not used for local, but kept for interface consistency)
        
        Returns:
            Upload endpoint URL with file_key parameter
        """
        encoded_key = quote(key, safe='')
        return f'/api/files/upload?file_key={encoded_key}'
