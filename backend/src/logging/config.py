import os
from logging import INFO, DEBUG

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_LEVEL_MAP = {
    'DEBUG': DEBUG,
    'INFO': INFO,
}

DEFAULT_LOG_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL, INFO)
