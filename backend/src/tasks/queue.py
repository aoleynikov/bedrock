from typing import Any, Optional
from src.tasks.celery.celery_app import celery_app
from src.logging.correlation import get_correlation_id


def enqueue(task_name: str, *args, correlation_id: Optional[str] = None, **kwargs) -> Any:
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    kwargs['correlation_id'] = correlation_id
    
    return celery_app.send_task(task_name, args=args, kwargs=kwargs)
