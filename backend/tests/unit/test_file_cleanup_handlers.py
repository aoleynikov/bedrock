from datetime import datetime

import pytest

from src.models.domain import UploadedFile
from src.tasks.file_cleanup.handlers import (
    AvatarFileCleanupHandler,
    DefaultFileCleanupHandler,
    FileCleanupHandler,
)


class FakeUploadedFileRepository:
    def __init__(self, files):
        self.files = files
        self.last_filter = None
        self.last_skip = None
        self.last_limit = None

    async def find_many(self, filter, skip=0, limit=100):
        self.last_filter = filter
        self.last_skip = skip
        self.last_limit = limit
        return self.files


class FakeFileStorageService:
    def __init__(self, delete_results=None, error_keys=None):
        self.delete_results = delete_results or {}
        self.error_keys = set(error_keys or [])

    async def delete_file(self, key):
        if key in self.error_keys:
            raise RuntimeError('delete failed')
        return self.delete_results.get(key, True)


class TestCleanupHandler(FileCleanupHandler):
    def __init__(self, uploaded_file_repository, file_storage_service, used_map):
        super().__init__(uploaded_file_repository, file_storage_service)
        self.used_map = used_map

    def get_file_type(self):
        return 'avatar'

    async def is_file_used(self, uploaded_file):
        return self.used_map.get(uploaded_file.file_key, False)


@pytest.mark.unit
@pytest.mark.asyncio
class TestFileCleanupHandler:
    async def test_cleanup_files_tracks_deleted_skipped_failed(self):
        files = [
            UploadedFile(
                file_key='used-file',
                owner_id='user-1',
                original_filename='a.png',
                file_size=10,
                created_at=datetime.utcnow()
            ),
            UploadedFile(
                file_key='deleted-file',
                owner_id='user-1',
                original_filename='b.png',
                file_size=10,
                created_at=datetime.utcnow()
            ),
            UploadedFile(
                file_key='failed-file',
                owner_id='user-1',
                original_filename='c.png',
                file_size=10,
                created_at=datetime.utcnow()
            ),
        ]
        repo = FakeUploadedFileRepository(files)
        storage = FakeFileStorageService(delete_results={'deleted-file': True, 'failed-file': False})
        handler = TestCleanupHandler(repo, storage, {'used-file': True})

        result = await handler.cleanup_files(max_age_hours=6, skip=0, limit=10)

        assert result['processed'] == 3
        assert result['deleted'] == 1
        assert result['skipped'] == 1
        assert result['failed'] == 1
        assert repo.last_skip == 0
        assert repo.last_limit == 10
        assert repo.last_filter['used_for'] == 'avatar'

    async def test_avatar_handler_requires_repository_for_usage_check(self):
        handler = AvatarFileCleanupHandler(
            FakeUploadedFileRepository([]),
            FakeFileStorageService(),
            None
        )
        file_record = UploadedFile(
            file_key='avatar-file',
            owner_id='user-1',
            original_filename='avatar.png',
            file_size=10
        )
        assert await handler.is_file_used(file_record) is False

    async def test_default_handler_filters_untyped_files(self):
        repo = FakeUploadedFileRepository([])
        handler = DefaultFileCleanupHandler(repo, FakeFileStorageService())

        result = await handler.cleanup_files(max_age_hours=6, skip=5, limit=20)

        assert result['file_type'] == 'untyped'
        assert repo.last_skip == 5
        assert repo.last_limit == 20
        assert '$or' in repo.last_filter
