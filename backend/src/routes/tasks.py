from fastapi import APIRouter, Request, Depends
from src.services.task_service import TaskService
from src.dependencies import get_task_service
from src.i18n.translator import get_translator
from src.exceptions.error_handlers import raise_translated_error
from src.auth.dependencies import get_current_user
from src.models.domain import User

router = APIRouter()


@router.post('/tasks/example')
async def create_example_task(
    request: Request,
    message: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """
    Create an example task.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    try:
        result = await task_service.create_example_task(message, correlation_id)
        return {
            'task_id': result['task_id'],
            'status': result['status'],
            'message': translator.t('messages.task_queued')
        }
    except ValueError as e:
        raise_translated_error(translator, e)


@router.get('/tasks/{task_id}')
async def get_task_status(
    request: Request,
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """
    Get task status by ID.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    try:
        return await task_service.get_task_status(task_id)
    except ValueError as e:
        raise_translated_error(translator, e)
