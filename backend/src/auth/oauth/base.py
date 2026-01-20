from abc import ABC, abstractmethod
from typing import Dict, Any
from src.auth.strategy import AuthenticationStrategy


class OAuthStrategy(AuthenticationStrategy, ABC):
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        pass

    @abstractmethod
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        pass
