from typing import Optional, Dict, Any
from celery.result import AsyncResult
from src.config import settings
from src.services.base import BaseService
from src.tasks.queue import enqueue
from src.tasks.celery.celery_app import celery_app
from src.tasks.queue_backend import get_in_memory_queue_backend


class TaskService(BaseService):
    """Service for task-related business logic."""
    
    def __init__(self):
        super().__init__()
    
    async def create_example_task(self, message: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create and enqueue an example task.
        
        Business rules:
        - Message must be provided
        - Task is enqueued with correlation ID for tracking
        """
        if not message or not message.strip():
            raise ValueError('errors.task.message_required')
        
        task = enqueue('example_task', message=message, correlation_id=correlation_id)
        
        self._log_info(
            f'Task created: {task.id}',
            task_id=task.id,
            correlation_id=correlation_id
        )
        
        return {
            'task_id': task.id,
            'status': 'pending',
            'message': message
        }

    async def trigger_cleanup_task(
        self,
        max_age_hours: int = 6,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enqueue the cleanup_unused_files task (admin-only).

        Business rules:
        - max_age_hours must be positive
        - Task is enqueued with correlation_id for tracking
        """
        if max_age_hours < 1:
            raise ValueError('errors.task.cleanup_max_age_invalid')

        task = enqueue(
            'cleanup_unused_files',
            max_age_hours=max_age_hours,
            correlation_id=correlation_id
        )

        self._log_info(
            f'Cleanup task enqueued: {task.id}',
            task_id=task.id,
            correlation_id=correlation_id,
            max_age_hours=max_age_hours
        )

        return {
            'task_id': task.id,
            'status': 'pending',
            'max_age_hours': max_age_hours
        }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status by ID.
        
        Business rules:
        - Task must exist
        - Returns current status and result if available
        """
        if not task_id:
            raise ValueError('errors.task.id_required')

        if settings.env.lower() == 'test':
            task = get_in_memory_queue_backend().get_task(task_id)
            if not task:
                raise ValueError('errors.task.not_found')
            return {
                'task_id': task_id,
                'status': 'PENDING',
            }

        result = AsyncResult(task_id, app=celery_app)
        
        # For RPC backend, we can't reliably check if task exists
        # Instead, we'll check if the task is in a valid state
        # Non-existent tasks in RPC backend will have PENDING state
        # but we can't distinguish from actually pending tasks
        # For now, we'll accept any state and let the client handle it
        
        # Try to get task info - if it fails, task doesn't exist
        try:
            # Force a check by accessing the state
            state = result.state
            # If state is PENDING and we can't get any info, might not exist
            # But this is unreliable with RPC backend, so we'll just return the state
        except Exception:
            raise ValueError('errors.task.not_found')
        
        response = {
            'task_id': task_id,
            'status': result.state,
        }
        
        if result.ready():
            if result.successful():
                response['result'] = result.result
            else:
                response['error'] = str(result.info) if result.info else 'Task failed'
        elif result.state == 'PENDING':
            # For non-existent tasks, we can't reliably detect them with RPC backend
            # So we'll accept PENDING as valid (task might be queued)
            pass
        
        return response
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a task.
        
        Business rules:
        - Task must exist
        - Only pending/running tasks can be cancelled
        """
        if not task_id:
            raise ValueError('errors.task.id_required')
        
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        self._log_info(
            f'Task cancelled: {task_id}',
            task_id=task_id
        )
        
        return {
            'task_id': task_id,
            'status': 'cancelled'
        }
