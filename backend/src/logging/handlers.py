import sys
from logging import StreamHandler
from src.logging.formatters import JSONFormatter


def create_stdout_handler() -> StreamHandler:
    handler = StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    return handler
