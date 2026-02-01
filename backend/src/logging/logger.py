import logging
from src.logging.config import DEFAULT_LOG_LEVEL
from src.logging.handlers import create_stdout_handler
from src.logging.correlation import get_correlation_id


class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        correlation_id = get_correlation_id()
        if correlation_id:
            kwargs.setdefault('extra', {})['correlation_id'] = correlation_id
        return msg, kwargs


def configure_root_logger() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(DEFAULT_LOG_LEVEL)
    if not root_logger.handlers:
        root_logger.addHandler(create_stdout_handler())


def get_logger(name: str, log_type: str = 'app') -> ContextLogger:
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOG_LEVEL)

    if not logger.handlers:
        logger.addHandler(create_stdout_handler())
    logger.propagate = False

    return ContextLogger(logger, {})
