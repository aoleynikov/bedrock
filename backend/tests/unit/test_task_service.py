from unittest.mock import MagicMock, patch

import pytest

from src.services.task_service import TaskService


@pytest.mark.unit
@pytest.mark.asyncio
class TestTaskService:
    async def test_create_example_task_success(self, task_service: TaskService):
        """Test successful task creation."""
        task_mock = MagicMock()
        task_mock.id = 'task-id'

        with patch('src.services.task_service.enqueue', return_value=task_mock) as enqueue_mock:
            result = await task_service.create_example_task('Test message', 'test-correlation-id')
        
        assert 'task_id' in result
        assert result['status'] == 'pending'
        assert result['message'] == 'Test message'
        enqueue_mock.assert_called_once_with(
            'example_task',
            message='Test message',
            correlation_id='test-correlation-id'
        )
    
    async def test_create_example_task_empty_message(self, task_service: TaskService):
        """Test task creation with empty message raises error."""
        with pytest.raises(ValueError, match='errors.task.message_required'):
            await task_service.create_example_task('', 'test-correlation-id')
    
    async def test_get_task_status_invalid_id(self, task_service: TaskService):
        """Test getting task status with invalid ID."""
        with pytest.raises(ValueError, match='errors.task.id_required'):
            await task_service.get_task_status('')

    async def test_trigger_cleanup_task_success(self, task_service: TaskService):
        """Test successful cleanup task enqueue."""
        task_mock = MagicMock()
        task_mock.id = 'cleanup-task-id'

        with patch('src.services.task_service.enqueue', return_value=task_mock) as enqueue_mock:
            result = await task_service.trigger_cleanup_task(6, 'corr-123')

        assert result['task_id'] == 'cleanup-task-id'
        assert result['status'] == 'pending'
        assert result['max_age_hours'] == 6
        enqueue_mock.assert_called_once_with(
            'cleanup_unused_files',
            max_age_hours=6,
            correlation_id='corr-123'
        )

    async def test_trigger_cleanup_task_invalid_max_age(self, task_service: TaskService):
        """Test cleanup with max_age_hours < 1 raises error."""
        with pytest.raises(ValueError, match='errors.task.cleanup_max_age_invalid'):
            await task_service.trigger_cleanup_task(0, None)
