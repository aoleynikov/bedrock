from datetime import datetime, timedelta

import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.tasks.file_cleanup.task import _run_cleanup_coordinator
from src.tasks.startup import _run_startup_tasks
from src.tasks.queue_backend import InMemoryQueueBackend


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cleanup_coordinator_enqueues_chunks(
    db_session: AsyncIOMotorDatabase,
    in_memory_queue: InMemoryQueueBackend,
) -> None:
    cutoff = datetime.utcnow() - timedelta(hours=10)
    collection = db_session['uploaded_files']
    await collection.insert_many(
        [
            {
                'file_key': 'avatar/test-avatar.png',
                'owner_id': 'user-1',
                'original_filename': 'avatar.png',
                'content_type': 'image/png',
                'file_size': 100,
                'used_for': 'avatar',
                'created_at': cutoff,
            },
            {
                'file_key': 'document/test-document.pdf',
                'owner_id': 'user-2',
                'original_filename': 'document.pdf',
                'content_type': 'application/pdf',
                'file_size': 200,
                'used_for': 'document',
                'created_at': cutoff,
            },
            {
                'file_key': 'misc/test-file.bin',
                'owner_id': 'user-3',
                'original_filename': 'file.bin',
                'content_type': 'application/octet-stream',
                'file_size': 300,
                'used_for': None,
                'created_at': cutoff,
            },
        ]
    )

    result = await _run_cleanup_coordinator(6, 'corr-id', 'task-id')

    assert result['chunks_created'] == 3
    assert result['tasks_queued'] == 3

    tasks = in_memory_queue.get_tasks()
    assert len(tasks) == 3
    assert {task.task_name for task in tasks} == {'process_cleanup_chunk'}
    assert {task.kwargs['file_type'] for task in tasks} == {'avatar', 'document', None}
    assert {task.kwargs['max_age_hours'] for task in tasks} == {6}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_startup_tasks_enqueue_default_admin(
    in_memory_queue: InMemoryQueueBackend,
) -> None:
    result = await _run_startup_tasks('corr-id', 'task-id')

    assert result['status'] == 'completed'
    assert result['tasks'] == ['ensure_default_admin']

    tasks = in_memory_queue.get_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.task_name == 'ensure_default_admin'
    assert task.kwargs['correlation_id'] == 'corr-id'
    assert result['task_ids'] == [task.task_id]
