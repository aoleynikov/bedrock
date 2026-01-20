import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if hasattr(record, 'correlation_id') and record.correlation_id:
            log_data['correlation_id'] = record.correlation_id

        if hasattr(record, 'endpoint') and record.endpoint:
            log_data['endpoint'] = record.endpoint

        if hasattr(record, 'task_name') and record.task_name:
            log_data['task_name'] = record.task_name

        if hasattr(record, 'task_id') and record.task_id:
            log_data['task_id'] = record.task_id

        if hasattr(record, 'duration') and record.duration is not None:
            log_data['duration_ms'] = record.duration

        if hasattr(record, 'status_code') and record.status_code:
            log_data['status_code'] = record.status_code

        if hasattr(record, 'method') and record.method:
            log_data['method'] = record.method

        if hasattr(record, 'path') and record.path:
            log_data['path'] = record.path

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data['stack'] = self.formatStack(record.stack_info)

        return json.dumps(log_data, ensure_ascii=False)
