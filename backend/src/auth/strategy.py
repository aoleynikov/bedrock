from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from fastapi import Request


class AuthenticationResult:
    def __init__(self, success: bool, user_id: Optional[str] = None, 
                 user_data: Optional[Dict[str, Any]] = None, 
                 error: Optional[str] = None):
        self.success = success
        self.user_id = user_id
        self.user_data = user_data or {}
        self.error = error


class AuthenticationStrategy(ABC):
    @abstractmethod
    async def authenticate(self, request: Request, **kwargs) -> AuthenticationResult:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
