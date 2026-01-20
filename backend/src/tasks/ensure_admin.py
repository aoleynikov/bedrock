import time
import asyncio
from typing import Dict, Any
from src.tasks.celery.celery_app import celery_app
from src.tasks.context import get_task_correlation_id, set_task_correlation_id
from src.tasks.metrics import celery_tasks_total, celery_task_duration_seconds
from src.logging.logger import get_logger
from src.database.connection import DatabaseConnection
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService

logger = get_logger(__name__, 'tasks')

@celery_app.task(name='ensure_default_admin', bind=True)
def ensure_default_admin(self, correlation_id: str = None) -> Dict[str, Any]:
    set_task_correlation_id(correlation_id)
    task_correlation_id = get_task_correlation_id()
    task_id = self.request.id
    start_time = time.time()

    logger.info(
        'Ensure default admin task started',
        extra={
            'correlation_id': task_correlation_id,
            'task_name': 'ensure_default_admin',
            'task_id': task_id
        }
    )

    try:
        result = asyncio.run(_run_ensure_default_admin(task_correlation_id, task_id))
        duration = time.time() - start_time

        celery_tasks_total.labels(
            task_name='ensure_default_admin',
            status='success'
        ).inc()

        celery_task_duration_seconds.labels(
            task_name='ensure_default_admin',
            status='success'
        ).observe(duration)

        logger.info(
            'Ensure default admin task completed',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'ensure_default_admin',
                'task_id': task_id,
                'duration': duration * 1000,
                **result
            }
        )

        return result
    except Exception as e:
        duration = time.time() - start_time

        celery_tasks_total.labels(
            task_name='ensure_default_admin',
            status='failure'
        ).inc()

        celery_task_duration_seconds.labels(
            task_name='ensure_default_admin',
            status='failure'
        ).observe(duration)

        logger.error(
            f'Ensure default admin task failed: {str(e)}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'ensure_default_admin',
                'task_id': task_id,
                'duration': duration * 1000,
            },
            exc_info=True,
        )
        raise


async def _run_ensure_default_admin(correlation_id: str, task_id: str) -> Dict[str, Any]:
    try:
        db = DatabaseConnection.get_db()
    except RuntimeError:
        await DatabaseConnection.connect()
        db = DatabaseConnection.get_db()

    user_repository = UserRepository(db)
    user_service = UserService(user_repository)

    admin_user = await user_service.ensure_default_admin()

    logger.info(
        'Ensure default admin completed',
        extra={
            'correlation_id': correlation_id,
            'task_id': task_id,
            'admin_user_id': admin_user.id,
            'admin_email': admin_user.email
        }
    )

    return {
        'status': 'completed',
        'admin_user_id': admin_user.id,
        'admin_email': admin_user.email,
        'admin_role': admin_user.role
    }
