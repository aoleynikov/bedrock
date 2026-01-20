from typing import Optional, List
from datetime import datetime
from src.services.base import BaseService
from src.config import settings
from src.services.file_storage_service import FileStorageService
from src.repositories.user_repository import UserRepository
from src.models.domain import User, UserCreate, UserResponse, AdminUserCreate
from src.services.password import hash_password


class UserService(BaseService):
    """Service for user-related business logic."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        file_storage_service: Optional[FileStorageService] = None
    ):
        super().__init__()
        self.user_repository = user_repository
        self.file_storage_service = file_storage_service
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Business rules:
        - Email must be unique
        - Password must be hashed before storage
        - Created timestamp is set automatically
        """
        # Check if user with email already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError('errors.user.email_exists')
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user entity
        user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password,
            role='user',
            created_at=datetime.utcnow()
        )
        
        # Save to repository
        created_user = await self.user_repository.create(user)
        
        self._log_info(
            f'User created: {created_user.id}',
            user_id=created_user.id,
            email=created_user.email
        )
        
        return created_user

    async def create_user_with_role(self, user_data: AdminUserCreate) -> User:
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError('errors.user.email_exists')

        hashed_password = hash_password(user_data.password)

        user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password,
            role=user_data.role,
            created_at=datetime.utcnow()
        )

        created_user = await self.user_repository.create(user)

        self._log_info(
            f'User created: {created_user.id}',
            user_id=created_user.id,
            email=created_user.email
        )

        return created_user

    async def ensure_default_admin(self) -> User:
        admin_user = await self.user_repository.find_one({'role': 'admin'})
        if admin_user:
            return admin_user

        default_email = settings.admin_default_email
        existing_user = await self.user_repository.get_by_email(default_email)
        if existing_user:
            existing_user.role = 'admin'
            updated_user = await self.user_repository.update(existing_user.id, existing_user)
            if updated_user is None:
                raise ValueError('errors.user.not_found')
            self._log_info(
                f'User promoted to admin: {updated_user.id}',
                user_id=updated_user.id,
                email=updated_user.email
            )
            return updated_user

        admin_data = AdminUserCreate(
            email=default_email,
            name=settings.admin_default_name,
            password=settings.admin_default_password,
            role='admin'
        )
        created_user = await self.create_user_with_role(admin_data)
        self._log_info(
            f'Admin user created: {created_user.id}',
            user_id=created_user.id,
            email=created_user.email
        )
        return created_user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        user = await self.user_repository.get_by_id(user_id)
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        user = await self.user_repository.get_by_email(email)
        return user
    
    async def get_user_or_raise(self, user_id: str) -> User:
        """
        Get user by ID or raise exception if not found.
        Used when user existence is required for the operation.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError('errors.user.not_found')
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        users = await self.user_repository.get_all(skip=skip, limit=limit)
        return users
    
    async def update_user(self, user_id: str, user_data: dict) -> User:
        """
        Update user information.
        
        Business rules:
        - User must exist
        - Email uniqueness is validated if email is being changed
        """
        user = await self.get_user_or_raise(user_id)
        
        # If email is being changed, check uniqueness
        if 'email' in user_data and user_data['email'] != user.email:
            existing_user = await self.user_repository.get_by_email(user_data['email'])
            if existing_user:
                raise ValueError('errors.user.email_exists')
            user.email = user_data['email']
        
        # Update other fields
        if 'name' in user_data:
            user.name = user_data['name']
        
        # Update password if provided
        if 'password' in user_data:
            user.hashed_password = hash_password(user_data['password'])
        
        updated_user = await self.user_repository.update(user_id, user)
        
        self._log_info(
            f'User updated: {updated_user.id}',
            user_id=updated_user.id
        )
        
        return updated_user
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Business rules:
        - User must exist
        """
        user = await self.get_user_or_raise(user_id)
        
        deleted = await self.user_repository.delete(user_id)
        
        if deleted:
            self._log_info(
                f'User deleted: {user_id}',
                user_id=user_id
            )
        
        return deleted

    async def delete_user_as_admin(self, user_id: str, current_user_id: str) -> bool:
        if user_id == current_user_id:
            raise ValueError('errors.user.cannot_delete_self')
        return await self.delete_user(user_id)
    
    async def set_avatar(self, user_id: str, file_key: str) -> User:
        """
        Set user avatar using file_key.
        
        Business rules:
        - User must exist
        - File must exist in storage
        - Old avatar is deleted if exists
        - User's avatar_file_key is updated
        """
        user = await self.get_user_or_raise(user_id)
        
        if not self.file_storage_service:
            raise ValueError('errors.file.storage_not_configured')
        
        # Verify file exists
        if not await self.file_storage_service.file_exists(file_key):
            raise ValueError('errors.file.not_found')
        
        # Delete old avatar if exists
        if user.avatar_file_key:
            try:
                await self.file_storage_service.delete_file(user.avatar_file_key)
            except Exception as e:
                self._log_warning(
                    f'Failed to delete old avatar: {user.avatar_file_key}',
                    error=e,
                    user_id=user_id
                )
        
        # Update user
        user.avatar_file_key = file_key
        updated_user = await self.user_repository.update(user_id, user)
        
        self._log_info(
            f'Avatar set for user: {user_id}',
            user_id=user_id,
            avatar_key=file_key
        )
        
        return updated_user
    
    async def delete_avatar(self, user_id: str) -> User:
        """
        Delete user avatar.
        
        Business rules:
        - User must exist
        - Avatar file is deleted from storage
        - User's avatar_file_key is cleared
        """
        user = await self.get_user_or_raise(user_id)
        
        if not user.avatar_file_key:
            return user  # No avatar to delete
        
        if self.file_storage_service:
            try:
                await self.file_storage_service.delete_file(user.avatar_file_key)
            except Exception as e:
                self._log_warning(
                    f'Failed to delete avatar file: {user.avatar_file_key}',
                    error=e,
                    user_id=user_id
                )
        
        # Clear avatar key
        user.avatar_file_key = None
        updated_user = await self.user_repository.update(user_id, user)
        
        if updated_user is None:
            raise ValueError('errors.user.not_found')
        
        self._log_info(
            f'Avatar deleted for user: {user_id}',
            user_id=user_id
        )
        
        return updated_user
    
    def to_response(self, user: User) -> UserResponse:
        """Convert User domain model to UserResponse DTO."""
        avatar_url = None
        if user.avatar_file_key and self.file_storage_service:
            avatar_url = self.file_storage_service.get_file_url(user.avatar_file_key)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_file_key=user.avatar_file_key,
            avatar_url=avatar_url,
            role=user.role,
            created_at=user.created_at
        )
