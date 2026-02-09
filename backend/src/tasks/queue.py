from typing import Any, Optional
from src.tasks.queue_backend import get_queue_backend
from src.logging.correlation import get_correlation_id


def enqueue(task_name: str, *args, correlation_id: Optional[str] = None, **kwargs) -> Any:
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    kwargs['correlation_id'] = correlation_id
    
    return get_queue_backend().send_task(task_name, *args, **kwargs)
