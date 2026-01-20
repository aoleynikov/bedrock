import pytest

from src.tasks import startup


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_startup_tasks_enqueues_default_admin(monkeypatch):
    class FakeTaskResult:
        def __init__(self, task_id):
            self.id = task_id

    def fake_enqueue(task_name: str, *args, **kwargs):
        return FakeTaskResult(f'{task_name}-id')

    monkeypatch.setattr(startup, 'enqueue', fake_enqueue)

    result = await startup._run_startup_tasks('corr-id', 'task-id')

    assert result['status'] == 'completed'
    assert result['tasks'] == ['ensure_default_admin']
    assert result['task_ids'] == ['ensure_default_admin-id']
