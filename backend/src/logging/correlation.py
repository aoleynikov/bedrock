import uuid
from contextvars import ContextVar
from typing import Optional

correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> Optional[str]:
    return correlation_id_var.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    correlation_id_var.set(None)
