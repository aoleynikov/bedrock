from fastapi import Depends, Request
from typing import Optional
from src.auth.service import auth_service
from src.repositories import get_user_repository
from src.repositories.user_repository import UserRepository
from src.models.domain import User
from src.exceptions import UnauthorizedException, ForbiddenException


async def get_current_user(
    request: Request,
    repo: UserRepository = Depends(get_user_repository)
) -> User:
    authorization = request.headers.get('Authorization')
    
    if not authorization:
        raise UnauthorizedException()
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise UnauthorizedException()
    except ValueError:
        raise UnauthorizedException()
    
    payload = auth_service.verify_access_token(token)
    if not payload:
        raise UnauthorizedException()
    
    user_id = payload.get('sub')
    if not user_id:
        raise UnauthorizedException()
    
    user = await repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException()
    
    return user


async def get_optional_user(
    request: Request,
    repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    try:
        return await get_current_user(request, repo)
    except UnauthorizedException:
        return None


def require_roles(*required_roles: str):
    async def _require_roles(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not required_roles:
            return current_user
        if current_user.role not in required_roles:
            raise ForbiddenException()
        return current_user

    return _require_roles
