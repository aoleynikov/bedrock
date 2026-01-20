from datetime import datetime, timedelta

import pytest

from src.repositories.uploaded_file_repository import UploadedFileRepository
from src.tasks.file_cleanup.pagination import create_cleanup_chunks, get_file_count_for_cleanup


@pytest.mark.integration
@pytest.mark.asyncio
class TestFileCleanupPaginationIntegration:
    async def test_get_file_count_for_cleanup_counts_by_type(self, db_session):
        repo = UploadedFileRepository(db_session)
        collection = repo._get_collection()
        old = datetime.utcnow() - timedelta(hours=7)
        new = datetime.utcnow() - timedelta(hours=1)

        await collection.insert_many(
            [
                {
                    'file_key': 'avatar-old',
                    'owner_id': 'user-1',
                    'original_filename': 'a.png',
                    'file_size': 10,
                    'used_for': 'avatar',
                    'created_at': old
                },
                {
                    'file_key': 'avatar-new',
                    'owner_id': 'user-1',
                    'original_filename': 'b.png',
                    'file_size': 10,
                    'used_for': 'avatar',
                    'created_at': new
                },
                {
                    'file_key': 'document-old',
                    'owner_id': 'user-1',
                    'original_filename': 'c.png',
                    'file_size': 10,
                    'used_for': 'document',
                    'created_at': old
                },
                {
                    'file_key': 'untyped-old',
                    'owner_id': 'user-1',
                    'original_filename': 'd.png',
                    'file_size': 10,
                    'created_at': old
                },
                {
                    'file_key': 'untyped-null',
                    'owner_id': 'user-1',
                    'original_filename': 'e.png',
                    'file_size': 10,
                    'used_for': None,
                    'created_at': old
                },
            ]
        )

        avatar_count = await get_file_count_for_cleanup(repo, 'avatar', 6)
        untyped_count = await get_file_count_for_cleanup(repo, None, 6)

        assert avatar_count == 1
        assert untyped_count == 2

    async def test_create_cleanup_chunks_uses_count(self, db_session):
        repo = UploadedFileRepository(db_session)
        collection = repo._get_collection()
        old = datetime.utcnow() - timedelta(hours=7)

        await collection.insert_many(
            [
                {
                    'file_key': 'avatar-old-1',
                    'owner_id': 'user-1',
                    'original_filename': 'a.png',
                    'file_size': 10,
                    'used_for': 'avatar',
                    'created_at': old
                },
                {
                    'file_key': 'avatar-old-2',
                    'owner_id': 'user-1',
                    'original_filename': 'b.png',
                    'file_size': 10,
                    'used_for': 'avatar',
                    'created_at': old
                },
            ]
        )

        chunks = await create_cleanup_chunks(repo, 'avatar', 6, chunk_size=1)

        assert len(chunks) == 2
        assert chunks[0]['skip'] == 0
        assert chunks[1]['skip'] == 1
