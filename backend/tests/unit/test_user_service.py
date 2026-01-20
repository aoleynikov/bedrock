import uuid

import pytest

from src.config import settings
from src.models.domain import User, UserCreate
from src.services.user_service import UserService


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    @pytest.fixture
    def user_repository(self):
        class FakeUserRepository:
            def __init__(self):
                self._users = {}

            async def get_by_email(self, email: str):
                for user in self._users.values():
                    if user.email == email:
                        return user
                return None

            async def find_one(self, filter: dict):
                for user in self._users.values():
                    if all(getattr(user, key, None) == value for key, value in filter.items()):
                        return user
                return None

            async def create(self, user: User):
                if not user.id:
                    user.id = str(uuid.uuid4())
                self._users[user.id] = user
                return user

            async def get_by_id(self, user_id: str):
                return self._users.get(user_id)

            async def update(self, user_id: str, user: User):
                if user_id not in self._users:
                    return None
                self._users[user_id] = user
                return user

            async def delete(self, user_id: str):
                return self._users.pop(user_id, None) is not None

            async def get_all(self, skip: int = 0, limit: int = 100):
                users = list(self._users.values())
                return users[skip:skip + limit]

        return FakeUserRepository()

    @pytest.fixture
    def user_service(self, user_repository):
        return UserService(user_repository)

    async def test_create_user_success(self, user_service: UserService):
        """Test successful user creation."""
        user_data = UserCreate(
            email='service_test@example.com',
            name='Service Test User',
            password='password123'
        )
        
        user = await user_service.create_user(user_data)
        
        assert user.id is not None
        assert user.email == 'service_test@example.com'
        assert user.name == 'Service Test User'
        assert user.hashed_password != 'password123'  # Should be hashed
    
    async def test_create_user_duplicate_email(self, user_service: UserService):
        """Test user creation with duplicate email raises error."""
        user_data = UserCreate(
            email='duplicate@example.com',
            name='First User',
            password='password123'
        )
        
        # Create first user
        await user_service.create_user(user_data)
        
        # Try to create second user with same email
        with pytest.raises(ValueError, match='errors.user.email_exists'):
            await user_service.create_user(user_data)
    
    async def test_get_user_by_id(self, user_service: UserService):
        """Test getting user by ID."""
        user_data = UserCreate(
            email='getbyid@example.com',
            name='Get By ID',
            password='password123'
        )
        created_user = await user_service.create_user(user_data)
        
        found_user = await user_service.get_user_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email
    
    async def test_get_user_by_id_not_found(self, user_service: UserService):
        """Test getting non-existent user returns None."""
        found_user = await user_service.get_user_by_id('nonexistent_id')
        assert found_user is None
    
    async def test_get_user_or_raise_found(self, user_service: UserService):
        """Test get_user_or_raise when user exists."""
        user_data = UserCreate(
            email='exists@example.com',
            name='Exists User',
            password='password123'
        )
        created_user = await user_service.create_user(user_data)
        
        user = await user_service.get_user_or_raise(created_user.id)
        assert user.id == created_user.id
    
    async def test_get_user_or_raise_not_found(self, user_service: UserService):
        """Test get_user_or_raise when user doesn't exist."""
        with pytest.raises(ValueError, match='errors.user.not_found'):
            await user_service.get_user_or_raise('nonexistent_id')
    
    async def test_update_user(self, user_service: UserService):
        """Test updating user."""
        user_data = UserCreate(
            email='update@example.com',
            name='Original Name',
            password='password123'
        )
        created_user = await user_service.create_user(user_data)
        
        updated_user = await user_service.update_user(
            created_user.id,
            {'name': 'Updated Name'}
        )
        
        assert updated_user.name == 'Updated Name'
        assert updated_user.email == 'update@example.com'
    
    async def test_update_user_email_duplicate(self, user_service: UserService):
        """Test updating user email to existing email raises error."""
        # Create two users
        user1_data = UserCreate(
            email='user1@example.com',
            name='User 1',
            password='password123'
        )
        user2_data = UserCreate(
            email='user2@example.com',
            name='User 2',
            password='password123'
        )
        user1 = await user_service.create_user(user1_data)
        await user_service.create_user(user2_data)
        
        # Try to update user1's email to user2's email
        with pytest.raises(ValueError, match='errors.user.email_exists'):
            await user_service.update_user(
                user1.id,
                {'email': 'user2@example.com'}
            )
    
    async def test_delete_user(self, user_service: UserService):
        """Test deleting user."""
        user_data = UserCreate(
            email='delete@example.com',
            name='Delete User',
            password='password123'
        )
        created_user = await user_service.create_user(user_data)
        
        deleted = await user_service.delete_user(created_user.id)
        
        assert deleted is True
        
        found_user = await user_service.get_user_by_id(created_user.id)
        assert found_user is None
    
    async def test_delete_user_not_found(self, user_service: UserService):
        """Test deleting non-existent user raises error."""
        with pytest.raises(ValueError, match='errors.user.not_found'):
            await user_service.delete_user('nonexistent_id')
    
    async def test_to_response(self, user_service: UserService):
        """Test converting User to UserResponse."""
        user_data = UserCreate(
            email='response@example.com',
            name='Response User',
            password='password123'
        )
        user = await user_service.create_user(user_data)
        
        response = user_service.to_response(user)
        
        assert response.id == user.id
        assert response.email == user.email
        assert response.name == user.name
        assert 'hashed_password' not in response.model_dump()  # Should not be in response

    async def test_ensure_default_admin_creates_admin(self, user_service: UserService, user_repository):
        admin_user = await user_service.ensure_default_admin()

        assert admin_user is not None
        assert admin_user.role == 'admin'
        assert admin_user.email == settings.admin_default_email
        assert admin_user.hashed_password != settings.admin_default_password
        assert len(user_repository._users) == 1

    async def test_ensure_default_admin_uses_existing_admin(self, user_service: UserService, user_repository):
        existing_admin = User(
            email='existing-admin@example.com',
            name='Existing Admin',
            hashed_password='hashed',
            role='admin'
        )
        await user_repository.create(existing_admin)

        admin_user = await user_service.ensure_default_admin()

        assert admin_user.id == existing_admin.id
        assert len(user_repository._users) == 1

    async def test_ensure_default_admin_promotes_default_user(self, user_service: UserService, user_repository):
        existing_user = User(
            email=settings.admin_default_email,
            name=settings.admin_default_name,
            hashed_password='hashed',
            role='user'
        )
        await user_repository.create(existing_user)

        admin_user = await user_service.ensure_default_admin()

        assert admin_user.id == existing_user.id
        assert admin_user.role == 'admin'
        assert admin_user.hashed_password == 'hashed'
