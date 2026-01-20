from fastapi import APIRouter, Depends, Request, status, Query, Response
from src.models.domain import UserResponse, UserCreate, AdminUserCreate
from src.services.user_service import UserService
from src.dependencies import get_user_service
from src.i18n.translator import get_translator
from src.auth.dependencies import require_roles

router = APIRouter()


@router.post('/users', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    
    Gateway: HTTP endpoint -> Service layer
    """
    translator = get_translator(request)
    
    try:
        created_user = await user_service.create_user(user_data)
        return user_service.to_response(created_user)
    except ValueError as e:
        from src.exceptions.error_handlers import raise_translated_error
        raise_translated_error(translator, e)


@router.post('/users/admin', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    request: Request,
    user_data: AdminUserCreate,
    current_user=Depends(require_roles('admin')),
    user_service: UserService = Depends(get_user_service)
):
    translator = get_translator(request)

    try:
        created_user = await user_service.create_user_with_role(user_data)
        return user_service.to_response(created_user)
    except ValueError as e:
        from src.exceptions.error_handlers import raise_translated_error
        raise_translated_error(translator, e)


@router.get('/users', response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(require_roles('admin')),
    user_service: UserService = Depends(get_user_service)
):
    users = await user_service.list_users(skip=skip, limit=limit)
    return [user_service.to_response(user) for user in users]


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str,
    current_user=Depends(require_roles('admin')),
    user_service: UserService = Depends(get_user_service)
):
    translator = get_translator(request)
    try:
        deleted = await user_service.delete_user_as_admin(user_id, current_user.id)
        if not deleted:
            raise ValueError('errors.user.not_found')
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        from src.exceptions.error_handlers import raise_translated_error
        error_key = str(e)
        if error_key == 'errors.user.cannot_delete_self':
            raise_translated_error(translator, e, status_code=status.HTTP_403_FORBIDDEN)
        if error_key == 'errors.user.not_found':
            raise_translated_error(translator, e, status_code=status.HTTP_404_NOT_FOUND)
        raise_translated_error(translator, e, status_code=status.HTTP_400_BAD_REQUEST)
