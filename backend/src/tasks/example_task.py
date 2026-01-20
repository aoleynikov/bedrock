import time
from src.tasks.celery.celery_app import celery_app
from src.tasks.context import get_task_correlation_id, set_task_correlation_id
from src.tasks.metrics import celery_tasks_total, celery_task_duration_seconds
from src.logging.logger import get_logger

logger = get_logger(__name__, 'tasks')

@celery_app.task(name='example_task', bind=True)
def example_task(self, message: str, correlation_id: str = None):
    set_task_correlation_id(correlation_id)
    task_correlation_id = get_task_correlation_id()
    task_id = self.request.id
    
    start_time = time.time()
    
    logger.info(
        f'Task example_task started: {message}',
        extra={
            'correlation_id': task_correlation_id,
            'task_name': 'example_task',
            'task_id': task_id,
        }
    )
    
    try:
        result = {'status': 'completed', 'message': message}
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='example_task',
            status='success'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='example_task',
            status='success'
        ).observe(duration)
        
        logger.info(
            f'Task example_task completed: {message}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'example_task',
                'task_id': task_id,
                'duration': duration * 1000,
            }
        )
        
        return result
    except Exception as e:
        duration = time.time() - start_time
        
        celery_tasks_total.labels(
            task_name='example_task',
            status='failure'
        ).inc()
        
        celery_task_duration_seconds.labels(
            task_name='example_task',
            status='failure'
        ).observe(duration)
        
        logger.error(
            f'Task example_task failed: {str(e)}',
            extra={
                'correlation_id': task_correlation_id,
                'task_name': 'example_task',
                'task_id': task_id,
                'duration': duration * 1000,
            },
            exc_info=True,
        )
        raise
