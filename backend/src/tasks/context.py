from typing import Optional
from celery import current_task
from src.logging.correlation import get_correlation_id, set_correlation_id


def get_task_correlation_id() -> Optional[str]:
    if current_task and current_task.request:
        return current_task.request.get('correlation_id')
    return get_correlation_id()


def set_task_correlation_id(correlation_id: Optional[str] = None) -> str:
    if correlation_id is None:
        correlation_id = get_correlation_id()
    
    if current_task and current_task.request:
        current_task.request.correlation_id = correlation_id
    
    if correlation_id:
        set_correlation_id(correlation_id)
    
    return correlation_id or ''
