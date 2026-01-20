from typing import Any, Dict, Iterator

import pytest
from httpx import AsyncClient
from kombu import Connection
from kombu.message import Message
from kombu.simple import SimpleQueue

from src.config import settings
from src.tasks.queue import enqueue


@pytest.fixture
def rabbitmq_connection() -> Iterator[Connection]:
    connection = Connection(settings.rabbitmq_url)
    try:
        connection.connect()
    except Exception:
        pytest.skip('RabbitMQ is not available')
    yield connection
    connection.release()


@pytest.fixture
def celery_test_queue(rabbitmq_connection: Connection) -> Iterator[SimpleQueue]:
    queue = rabbitmq_connection.SimpleQueue('celery')
    queue.clear()
    yield queue
    queue.clear()
    queue.close()


def _receive_message(queue: SimpleQueue, timeout: int = 5) -> Message:
    try:
        return queue.get(timeout=timeout)
    except queue.Empty:
        pytest.fail('No celery message received')


def _extract_task_message(message: Message) -> Dict[str, Any]:
    payload = message.payload
    if isinstance(payload, (list, tuple)) and len(payload) >= 2:
        args = payload[0]
        kwargs = payload[1]
    elif isinstance(payload, dict):
        args = payload.get('args', [])
        kwargs = payload.get('kwargs', {})
    else:
        args = []
        kwargs = {}
    headers = message.headers or {}
    return {
        'task': headers.get('task'),
        'args': args,
        'kwargs': kwargs,
        'id': headers.get('id'),
    }


@pytest.mark.integration
class TestCeleryQueue:
    async def test_create_example_task_enqueues_message(
        self,
        authenticated_client: AsyncClient,
        celery_test_queue: SimpleQueue,
    ) -> None:
        correlation_id = 'test-correlation-id'
        response = await authenticated_client.post(
            '/api/tasks/example',
            params={'message': 'Test task message'},
            headers={'X-Correlation-ID': correlation_id},
        )

        assert response.status_code == 200
        message = _receive_message(celery_test_queue)
        payload = _extract_task_message(message)
        message.ack()

        assert payload['task'] == 'example_task'
        assert payload['kwargs']['message'] == 'Test task message'
        assert payload['kwargs']['correlation_id'] == correlation_id

    def test_enqueue_example_task_job(self, celery_test_queue: SimpleQueue) -> None:
        correlation_id = 'test-correlation-id'
        enqueue('example_task', message='Queue test', correlation_id=correlation_id)

        message = _receive_message(celery_test_queue)
        payload = _extract_task_message(message)
        message.ack()

        assert payload['task'] == 'example_task'
        assert payload['kwargs']['message'] == 'Queue test'
        assert payload['kwargs']['correlation_id'] == correlation_id

    def test_enqueue_cleanup_unused_files_job(self, celery_test_queue: SimpleQueue) -> None:
        correlation_id = 'test-correlation-id'
        enqueue('cleanup_unused_files', max_age_hours=12, correlation_id=correlation_id)

        message = _receive_message(celery_test_queue)
        payload = _extract_task_message(message)
        message.ack()

        assert payload['task'] == 'cleanup_unused_files'
        assert payload['kwargs']['max_age_hours'] == 12
        assert payload['kwargs']['correlation_id'] == correlation_id

    def test_enqueue_process_cleanup_chunk_job(self, celery_test_queue: SimpleQueue) -> None:
        correlation_id = 'test-correlation-id'
        enqueue(
            'process_cleanup_chunk',
            file_type='avatar',
            skip=10,
            limit=5,
            max_age_hours=6,
            correlation_id=correlation_id,
        )

        message = _receive_message(celery_test_queue)
        payload = _extract_task_message(message)
        message.ack()

        assert payload['task'] == 'process_cleanup_chunk'
        assert payload['kwargs']['file_type'] == 'avatar'
        assert payload['kwargs']['skip'] == 10
        assert payload['kwargs']['limit'] == 5
        assert payload['kwargs']['max_age_hours'] == 6
        assert payload['kwargs']['correlation_id'] == correlation_id
