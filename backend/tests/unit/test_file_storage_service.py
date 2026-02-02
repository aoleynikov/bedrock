import tempfile

import pytest

from src.services.file_storage_service import FileStorageService
from src.storage.local_file_store import LocalFileStore


class AsyncBytesReader:
    def __init__(self, data: bytes):
        self.data = data
        self.offset = 0

    async def read(self, size: int):
        if self.offset >= len(self.data):
            return b''
        chunk = self.data[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class FailingUploadedFileRepository:
    async def create(self, uploaded_file):
        raise RuntimeError('create failed')


@pytest.mark.unit
@pytest.mark.asyncio
class TestFileStorageService:
    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = LocalFileStore(base_path=tmpdir)
            yield storage
    
    @pytest.fixture
    def file_storage_service(self, temp_storage):
        """Create a file storage service with temporary storage."""
        return FileStorageService(temp_storage)
    
    async def test_generate_key_with_prefix(self, file_storage_service: FileStorageService):
        """Test key generation with prefix (prefix is ignored, format is uuid/filename)."""
        key = file_storage_service.generate_key(prefix='avatars', original_filename='test.jpg')
        
        # Format should be uuid/filename.ext (prefix is ignored)
        assert key.endswith('/test.jpg')
        parts = key.split('/')
        assert len(parts) == 2
        assert parts[1] == 'test.jpg'
        # First part should be a UUID (36 chars with dashes)
        assert len(parts[0]) == 36
        assert parts[0].count('-') == 4
    
    async def test_generate_key_without_prefix(self, file_storage_service: FileStorageService):
        """Test key generation without prefix."""
        key = file_storage_service.generate_key(original_filename='test.png')
        
        assert not key.startswith('/')
        assert key.endswith('/test.png')
        parts = key.split('/')
        assert len(parts) == 2
        assert parts[1] == 'test.png'
        # First part should be a UUID (36 chars with dashes)
        assert len(parts[0]) == 36
        assert parts[0].count('-') == 4
    
    async def test_store_file(self, file_storage_service: FileStorageService):
        """Test storing a file."""
        file_data = b'test file content'
        key = await file_storage_service.store_file(
            file_data=file_data,
            content_type='text/plain',
            original_filename='test.txt'
        )
        
        assert key is not None
        assert key.endswith('/test.txt')
        # Format should be uuid/filename.ext (prefix is ignored)
        parts = key.split('/')
        assert len(parts) == 2
        
        # Verify file exists
        exists = await file_storage_service.file_exists(key)
        assert exists is True
    
    async def test_store_file_empty_data(self, file_storage_service: FileStorageService):
        """Test storing empty file raises error."""
        with pytest.raises(ValueError, match='errors.file.empty'):
            await file_storage_service.store_file(file_data=b'')
    
    async def test_retrieve_file(self, file_storage_service: FileStorageService):
        """Test retrieving a file."""
        file_data = b'retrieved content'
        key = await file_storage_service.store_file(
            file_data=file_data
        )
        
        retrieved = await file_storage_service.retrieve_file(key)
        
        assert retrieved == file_data
    
    async def test_retrieve_file_not_found(self, file_storage_service: FileStorageService):
        """Test retrieving non-existent file."""
        retrieved = await file_storage_service.retrieve_file('nonexistent_key')
        
        assert retrieved is None
    
    async def test_delete_file(self, file_storage_service: FileStorageService):
        """Test deleting a file."""
        file_data = b'to be deleted'
        key = await file_storage_service.store_file(
            file_data=file_data
        )
        
        deleted = await file_storage_service.delete_file(key)
        
        assert deleted is True
        
        # Verify file no longer exists
        exists = await file_storage_service.file_exists(key)
        assert exists is False
    
    async def test_delete_file_not_found(self, file_storage_service: FileStorageService):
        """Test deleting non-existent file."""
        deleted = await file_storage_service.delete_file('nonexistent_key')
        
        assert deleted is False
    
    async def test_file_exists(self, file_storage_service: FileStorageService):
        """Test checking file existence."""
        file_data = b'exists test'
        key = await file_storage_service.store_file(
            file_data=file_data
        )
        
        exists = await file_storage_service.file_exists(key)
        assert exists is True
        
        # Delete and check again
        await file_storage_service.delete_file(key)
        exists = await file_storage_service.file_exists(key)
        assert exists is False
    
    async def test_get_file_url(self, file_storage_service: FileStorageService):
        """Test getting file URL."""
        key = 'test/file.jpg'
        url = file_storage_service.get_file_url(key)
        
        assert url is not None
        assert key in url
    
    async def test_extract_original_filename(self, file_storage_service: FileStorageService):
        """Test extracting original filename from key."""
        key = '550e8400-e29b-41d4-a716-446655440000/myphoto.jpg'
        filename = file_storage_service.extract_original_filename(key)
        
        assert filename == 'myphoto.jpg'
        
        key2 = '550e8400-e29b-41d4-a716-446655440000/document.pdf'
        filename2 = file_storage_service.extract_original_filename(key2)
        
        assert filename2 == 'document.pdf'
    
    async def test_generate_upload_url(self, file_storage_service: FileStorageService):
        """Test generating upload URL."""
        result = await file_storage_service.generate_upload_url(
            filename='test.jpg',
            content_type='image/jpeg',
            prefix='avatars'
        )
        
        assert 'file_key' in result
        assert 'upload_url' in result
        assert 'method' in result
        # Format should be uuid/filename.ext (prefix is ignored)
        assert result['file_key'].endswith('/test.jpg')
        parts = result['file_key'].split('/')
        assert len(parts) == 2

    async def test_store_file_stream_cleanup_on_size_exceeds(self, temp_storage):
        file_storage_service = FileStorageService(temp_storage)
        file_data = b'x' * 1024
        file_stream = AsyncBytesReader(file_data)
        custom_key = '550e8400-e29b-41d4-a716-446655440000/large.txt'

        with pytest.raises(ValueError, match='errors.file.size_exceeds'):
            await file_storage_service.store_file_stream(
                file_stream=file_stream,
                custom_key=custom_key,
                max_size=10
            )

        exists = await file_storage_service.file_exists(custom_key)
        assert exists is False

    async def test_store_file_stream_cleanup_on_record_failure(self, temp_storage):
        file_storage_service = FileStorageService(temp_storage, FailingUploadedFileRepository())
        file_data = b'content'
        file_stream = AsyncBytesReader(file_data)
        custom_key = '550e8400-e29b-41d4-a716-446655440000/record.txt'

        with pytest.raises(ValueError, match='errors.file.record_create_failed'):
            await file_storage_service.store_file_stream(
                file_stream=file_stream,
                custom_key=custom_key,
                owner_id='user-1'
            )

        exists = await file_storage_service.file_exists(custom_key)
        assert exists is False
    
