from celery.signals import worker_ready
from prometheus_client import start_http_server
from src.config import settings
from src.logging.logger import get_logger

logger = get_logger(__name__, 'tasks')
metrics_server_started = False


@worker_ready.connect
def start_metrics_server(**kwargs):
    global metrics_server_started
    if metrics_server_started:
        return
    start_http_server(settings.worker_metrics_port)
    logger.info(
        'Worker metrics server started',
        extra={'port': settings.worker_metrics_port}
    )
    metrics_server_started = True
