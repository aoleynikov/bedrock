import pytest

from src.tasks.celery.celery_app import celery_app
from src.worker import celery


@pytest.mark.unit
class TestWorker:
    def test_worker_exports_celery_app(self):
        assert celery is celery_app
