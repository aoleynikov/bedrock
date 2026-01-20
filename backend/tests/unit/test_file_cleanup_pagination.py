import pytest

from src.tasks.file_cleanup.pagination import create_cleanup_chunks, get_file_count_for_cleanup


class FakeCollection:
    def __init__(self, count):
        self.count = count
        self.last_filter = None

    async def count_documents(self, filter_query):
        self.last_filter = filter_query
        return self.count


class FakeUploadedFileRepository:
    def __init__(self, count):
        self.collection = FakeCollection(count)

    def _get_collection(self):
        return self.collection


@pytest.mark.unit
@pytest.mark.asyncio
class TestFileCleanupPagination:
    async def test_get_file_count_for_cleanup_uses_type_filter(self):
        repo = FakeUploadedFileRepository(7)
        count = await get_file_count_for_cleanup(repo, 'avatar', 6)

        assert count == 7
        assert repo.collection.last_filter['used_for'] == 'avatar'

    async def test_create_cleanup_chunks_builds_expected_chunks(self):
        repo = FakeUploadedFileRepository(5)
        chunks = await create_cleanup_chunks(repo, None, 6, chunk_size=2)

        assert len(chunks) == 3
        assert chunks[0]['skip'] == 0
        assert chunks[1]['skip'] == 2
        assert chunks[2]['skip'] == 4
        assert chunks[0]['file_type'] is None
