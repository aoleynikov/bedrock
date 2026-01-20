import pytest
from src.repositories.user_repository import UserRepository
from src.models.domain import User
from src.services.password import hash_password
from datetime import datetime


@pytest.mark.integration
class TestUserRepository:
    async def test_create_user(self, user_repository: UserRepository):
        """Test creating a user."""
        user = User(
            email='repo_test@example.com',
            name='Repo Test User',
            hashed_password=hash_password('password123'),
            created_at=datetime.utcnow()
        )
        
        created_user = await user_repository.create(user)
        
        assert created_user.id is not None
        assert created_user.email == 'repo_test@example.com'
        assert created_user.name == 'Repo Test User'
    
    async def test_get_by_id(self, user_repository: UserRepository):
        """Test getting user by ID."""
        user = User(
            email='getbyid@example.com',
            name='Get By ID User',
            hashed_password=hash_password('password123'),
            created_at=datetime.utcnow()
        )
        created_user = await user_repository.create(user)
        
        found_user = await user_repository.get_by_id(created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email
    
    async def test_get_by_id_not_found(self, user_repository: UserRepository):
        """Test getting user by non-existent ID."""
        found_user = await user_repository.get_by_id('nonexistent_id')
        
        assert found_user is None
    
    async def test_get_by_email(self, user_repository: UserRepository):
        """Test getting user by email."""
        user = User(
            email='getbyemail@example.com',
            name='Get By Email User',
            hashed_password=hash_password('password123'),
            created_at=datetime.utcnow()
        )
        created_user = await user_repository.create(user)
        
        found_user = await user_repository.get_by_email('getbyemail@example.com')
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == 'getbyemail@example.com'
    
    async def test_get_by_email_not_found(self, user_repository: UserRepository):
        """Test getting user by non-existent email."""
        found_user = await user_repository.get_by_email('nonexistent@example.com')
        
        assert found_user is None
    
    async def test_find_all(self, user_repository: UserRepository):
        """Test finding all users."""
        # Create multiple users
        for i in range(3):
            user = User(
                email=f'findall{i}@example.com',
                name=f'Find All User {i}',
                hashed_password=hash_password('password123'),
                created_at=datetime.utcnow()
            )
            await user_repository.create(user)
        
        users = await user_repository.find_all()
        
        assert len(users) >= 3
    
    async def test_update_user(self, user_repository: UserRepository):
        """Test updating a user."""
        user = User(
            email='update@example.com',
            name='Original Name',
            hashed_password=hash_password('password123'),
            created_at=datetime.utcnow()
        )
        created_user = await user_repository.create(user)
        
        created_user.name = 'Updated Name'
        updated_user = await user_repository.update(created_user.id, created_user)
        
        assert updated_user.name == 'Updated Name'
        assert updated_user.email == 'update@example.com'
    
    async def test_delete_user(self, user_repository: UserRepository):
        """Test deleting a user."""
        user = User(
            email='delete@example.com',
            name='Delete User',
            hashed_password=hash_password('password123'),
            created_at=datetime.utcnow()
        )
        created_user = await user_repository.create(user)
        
        deleted = await user_repository.delete(created_user.id)
        
        assert deleted is True
        
        found_user = await user_repository.get_by_id(created_user.id)
        assert found_user is None
