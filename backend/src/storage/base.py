from abc import ABC, abstractmethod
from typing import Optional


class FileStorage(ABC):
    """Abstract base class for file storage implementations."""
    
    @abstractmethod
    async def store(self, key: str, file_data: bytes, content_type: Optional[str] = None) -> str:
        """
        Store a file with the given key.
        
        Args:
            key: Unique identifier for the file
            file_data: File content as bytes
            content_type: MIME type of the file (optional)
        
        Returns:
            The storage key/path where the file was stored
        """
        pass
    
    @abstractmethod
    async def store_stream(self, key: str, file_stream, content_type: Optional[str] = None) -> str:
        """
        Store a file from a stream with the given key.
        
        Args:
            key: Unique identifier for the file
            file_stream: File content as an async iterator or file-like object
            content_type: MIME type of the file (optional)
        
        Returns:
            The storage key/path where the file was stored
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[bytes]:
        """
        Retrieve a file by its key.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            File content as bytes, or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a file by its key.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_url(self, key: str) -> str:
        """
        Get a URL or path to access the file.
        
        Args:
            key: Unique identifier for the file
        
        Returns:
            URL or path to the file
        """
        pass
    
    @abstractmethod
    def generate_presigned_upload_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned upload URL for direct file uploads.
        
        Args:
            key: Unique identifier for the file
            content_type: MIME type of the file
            expires_in: Expiration time in seconds (default: 3600)
        
        Returns:
            Presigned URL for S3, or regular upload endpoint for local storage
        """
        pass
