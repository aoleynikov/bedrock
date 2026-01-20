from fastapi import Request
from src.auth.strategy import AuthenticationStrategy, AuthenticationResult
from src.repositories import get_user_repository
from src.repositories.user_repository import UserRepository
from src.services.password import verify_password


class CredentialsStrategy(AuthenticationStrategy):
    def __init__(self):
        self._repo: UserRepository = None

    def _get_repo(self) -> UserRepository:
        if self._repo is None:
            self._repo = get_user_repository()
        return self._repo

    async def authenticate(self, request: Request, email: str = None, 
                         password: str = None, **kwargs) -> AuthenticationResult:
        if not email or not password:
            return AuthenticationResult(
                success=False,
                error='Email and password are required'
            )

        repo = self._get_repo()
        user = await repo.get_by_email(email)

        if not user:
            return AuthenticationResult(
                success=False,
                error='Invalid credentials'
            )

        if not verify_password(password, user.hashed_password):
            return AuthenticationResult(
                success=False,
                error='Invalid credentials'
            )

        return AuthenticationResult(
            success=True,
            user_id=user.id,
            user_data={
                'id': user.id,
                'email': user.email,
                'name': user.name,
            }
        )

    def get_name(self) -> str:
        return 'credentials'
