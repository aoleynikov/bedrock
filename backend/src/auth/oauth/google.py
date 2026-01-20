import httpx
from typing import Dict, Any
from fastapi import Request
from src.auth.oauth.base import OAuthStrategy
from src.auth.strategy import AuthenticationResult
from src.config import settings


class GoogleOAuthStrategy(OAuthStrategy):
    AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

    def __init__(self):
        super().__init__(
            client_id=settings.google_oauth_client_id or '',
            client_secret=settings.google_oauth_client_secret or '',
            redirect_uri=settings.google_oauth_redirect_uri or ''
        )

    async def get_authorization_url(self, state: str) -> str:
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent',
        }
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'{self.AUTHORIZATION_URL}?{query_string}'

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    'code': code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': self.redirect_uri,
                    'grant_type': 'authorization_code',
                }
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()

    async def authenticate(self, request: Request, code: str = None, 
                         access_token: str = None, **kwargs) -> AuthenticationResult:
        if code:
            tokens = await self.exchange_code_for_tokens(code)
            access_token = tokens.get('access_token')
        
        if not access_token:
            return AuthenticationResult(
                success=False,
                error='Access token or authorization code required'
            )

        try:
            user_info = await self.get_user_info(access_token)
            
            return AuthenticationResult(
                success=True,
                user_id=user_info.get('id'),
                user_data={
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'provider': 'google',
                    'provider_id': user_info.get('id'),
                }
            )
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error=f'Failed to authenticate with Google: {str(e)}'
            )

    def get_name(self) -> str:
        return 'google'
