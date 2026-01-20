from abc import ABC
from typing import Optional
from src.logging.logger import get_logger


class BaseService(ABC):
    """Base service class providing common functionality."""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def _log_info(self, message: str, **kwargs):
        """Log info message with optional context."""
        self.logger.info(message, extra=kwargs)
    
    def _log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception."""
        if error:
            self.logger.error(message, extra=kwargs, exc_info=error)
        else:
            self.logger.error(message, extra=kwargs)
    
    def _log_warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        self.logger.warning(message, extra=kwargs)
