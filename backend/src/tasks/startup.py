import time
import asyncio
from typing import Dict, Any
from src.tasks.celery.celery_app import celery_app
from src.tasks.context import get_task_correlation_id, set_task_correlation_id
from src.tasks.queue import enqueue
from src.tasks.metrics import celery_tasks_total, celery_task_duration_seconds
from src.logging.logger import get_logger

logger = get_logger(__name__, 'tasks')

@celery_app.task(name='startup_tasks', bind=True)
def startup_tasks(self, correlation_id: str = None) -> Dict[str, Any]:
    set_task_correlation_id(correlation_id)
    task_correlation_id = get_task_correlation_id()
    task_id = self.request.id
    start_time = time.time()

    logger.info(
        'Startup tasks started',
        extra={
            'correlation_id': task_correlation_id,
            'task_name': 'startup_tasks',
            'task_id': task_id
        }
    )

    try:
        result = asyncio.run(_run_startup_tasks(task_correlation_id, task_id))
        duration = time.time() - start_time

        celery_tasks_total.labels(
            task_name='startup_tasks',
            status='success'
        ).inc()

        celery_task_duration_seconds.labels(
            task_name='startup_tasks',
            status='success'
        ).observe(duration)

        logger.info(
            'Startup tasks completed',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'startup_tasks',
                'task_id': task_id,
                'duration': duration * 1000,
                **result
            }
        )

        return result
    except Exception as e:
        duration = time.time() - start_time

        celery_tasks_total.labels(
            task_name='startup_tasks',
            status='failure'
        ).inc()

        celery_task_duration_seconds.labels(
            task_name='startup_tasks',
            status='failure'
        ).observe(duration)

        logger.error(
            f'Startup tasks failed: {str(e)}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'startup_tasks',
                'task_id': task_id,
                'duration': duration * 1000,
            },
            exc_info=True,
        )
        raise


async def _run_startup_tasks(correlation_id: str, task_id: str) -> Dict[str, Any]:
    task = enqueue('ensure_default_admin', correlation_id=correlation_id)
    logger.info(
        'Startup task enqueued',
        extra={
            'correlation_id': correlation_id,
            'task_id': task_id,
            'startup_task': 'ensure_default_admin',
            'startup_task_id': task.id
        }
    )
    return {
        'status': 'completed',
        'tasks': ['ensure_default_admin'],
        'task_ids': [task.id]
    }
