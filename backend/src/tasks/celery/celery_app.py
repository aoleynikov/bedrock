import logging
from celery import Celery
from celery.signals import setup_logging
from celery.schedules import crontab
from src.config import settings
from src.logging.logger import configure_root_logger
from src.tasks.celery import metrics_server

celery_app = Celery(
    'bedrock_worker',
    broker=settings.rabbitmq_url,
    backend='rpc://',  # Use RPC backend for result storage (in-memory, fast for development)
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
    imports=('src.tasks.example_task', 'src.tasks.file_cleanup.task', 'src.tasks.file_cleanup.pagination', 'src.tasks.ensure_admin', 'src.tasks.startup'),
    autodiscover_tasks=['src.tasks'],
    beat_schedule={
        'cleanup-unused-files': {
            'task': 'cleanup_unused_files',
            'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours at :00
            'args': (6,)  # Clean up files older than 6 hours
        },
    },
)


@setup_logging.connect
def _configure_celery_logging(*args, **kwargs):
    configure_root_logger()
    logging.getLogger('celery').setLevel(logging.INFO)
