from dataclasses import dataclass
from typing import Any, Optional
from uuid import uuid4

from src.config import settings
from src.tasks.celery.celery_app import celery_app


@dataclass(frozen=True)
class QueuedTask:
    task_name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    task_id: str


@dataclass(frozen=True)
class InMemoryTaskResult:
    id: str


class TaskQueueBackend:
    """Queue backend interface."""

    def send_task(self, task_name: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class CeleryQueueBackend(TaskQueueBackend):
    """Queue backend that delegates to Celery."""

    def send_task(self, task_name: str, *args: Any, **kwargs: Any) -> Any:
        return celery_app.send_task(task_name, args=args, kwargs=kwargs)


class InMemoryQueueBackend(TaskQueueBackend):
    """Queue backend that records tasks in memory."""

    def __init__(self) -> None:
        self._tasks: list[QueuedTask] = []

    def send_task(self, task_name: str, *args: Any, **kwargs: Any) -> InMemoryTaskResult:
        task_id = uuid4().hex
        record = QueuedTask(
            task_name=task_name,
            args=tuple(args),
            kwargs=dict(kwargs),
            task_id=task_id,
        )
        self._tasks.append(record)
        return InMemoryTaskResult(id=task_id)

    def get_tasks(self) -> list[QueuedTask]:
        return list(self._tasks)

    def get_task(self, task_id: str) -> Optional[QueuedTask]:
        for task in self._tasks:
            if task.task_id == task_id:
                return task
        return None

    def clear(self) -> None:
        self._tasks.clear()


_IN_MEMORY_BACKEND = InMemoryQueueBackend()
_CELERY_BACKEND = CeleryQueueBackend()


def get_queue_backend() -> TaskQueueBackend:
    """Return the configured queue backend."""
    if settings.env.lower() == 'test':
        return _IN_MEMORY_BACKEND
    return _CELERY_BACKEND


def get_in_memory_queue_backend() -> InMemoryQueueBackend:
    """Return the in-memory queue backend."""
    return _IN_MEMORY_BACKEND
