from typing import Dict, Any, Optional
from fastapi import Request
from src.auth.strategy import AuthenticationStrategy, AuthenticationResult
from src.auth.credentials import CredentialsStrategy
from src.auth.oauth.google import GoogleOAuthStrategy
from src.auth.jwt import create_access_token, create_refresh_token, verify_token
from src.repositories import get_user_repository
from src.repositories.user_repository import UserRepository
from src.models.domain import User
from datetime import datetime, timedelta
from src.config import settings


class AuthenticationService:
    def __init__(self):
        self._strategies: Dict[str, AuthenticationStrategy] = {
            'credentials': CredentialsStrategy(),
            'google': GoogleOAuthStrategy(),
        }
        self._repo: UserRepository = None

    def _get_repo(self) -> UserRepository:
        if self._repo is None:
            self._repo = get_user_repository()
        return self._repo

    def get_strategy(self, strategy_name: str) -> Optional[AuthenticationStrategy]:
        return self._strategies.get(strategy_name)

    async def authenticate(self, strategy_name: str, request: Request, **kwargs) -> AuthenticationResult:
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            return AuthenticationResult(
                success=False,
                error=f'Unknown authentication strategy: {strategy_name}'
            )

        result = await strategy.authenticate(request, **kwargs)
        
        if result.success:
            repo = self._get_repo()
            user = None
            
            if result.user_id:
                user = await repo.get_by_id(result.user_id)
            
            if not user and 'email' in result.user_data:
                user = await repo.get_by_email(result.user_data['email'])
            
            if not user and 'email' in result.user_data:
                user = User(
                    email=result.user_data['email'],
                    name=result.user_data.get('name', ''),
                    hashed_password='',
                    role='user',
                    created_at=datetime.utcnow()
                )
                user = await repo.create(user)
            
            if user:
                result.user_id = user.id
                result.user_data.update({
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'role': user.role,
                })

        return result

    def create_tokens(self, user_id: str, email: str, role: str) -> Dict[str, str]:
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={'sub': user_id, 'email': email, 'role': role},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={'sub': user_id, 'email': email, 'role': role}
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        payload = verify_token(token)
        if payload and payload.get('type') != 'refresh':
            return payload
        return None

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        payload = verify_token(token)
        if payload and payload.get('type') == 'refresh':
            return payload
        return None

    async def get_oauth_authorization_url(self, strategy_name: str, state: str) -> Optional[str]:
        strategy = self.get_strategy(strategy_name)
        if not strategy or not hasattr(strategy, 'get_authorization_url'):
            return None
        
        return await strategy.get_authorization_url(state)


auth_service = AuthenticationService()
