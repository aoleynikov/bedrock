import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestUserRoutes:
    async def test_create_user_success(self, async_client: AsyncClient):
        """Test successful user creation."""
        response = await async_client.post(
            '/api/users',
            json={
                'email': 'newuser@example.com',
                'name': 'New User',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'newuser@example.com'
        assert data['name'] == 'New User'
        assert 'id' in data
        assert 'password' not in data
        assert 'hashed_password' not in data
    
    async def test_create_user_duplicate_email(self, async_client: AsyncClient, test_user):
        """Test user creation with duplicate email."""
        response = await async_client.post(
            '/api/users',
            json={
                'email': test_user['email'],
                'name': 'Duplicate User',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
    
    async def test_create_user_invalid_email(self, async_client: AsyncClient):
        """Test user creation with invalid email."""
        response = await async_client.post(
            '/api/users',
            json={
                'email': 'invalid-email',
                'name': 'Test User',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data
    
    async def test_create_user_short_password(self, async_client: AsyncClient):
        """Test user creation with password too short."""
        response = await async_client.post(
            '/api/users',
            json={
                'email': 'user@example.com',
                'name': 'Test User',
                'password': 'short'
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data

    async def test_list_users_unauthenticated(self, async_client: AsyncClient):
        """Test listing users without authentication."""
        response = await async_client.get('/api/users')

        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_list_users_forbidden_for_regular_user(self, authenticated_client: AsyncClient, test_user):
        """Test listing users as regular user (should be forbidden)."""
        response = await authenticated_client.get('/api/users')

        assert response.status_code == 403
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_list_users_admin(self, async_client: AsyncClient, admin_client: AsyncClient):
        """Test listing users as admin."""
        response = await admin_client.get('/api/users')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_admin_create_user_with_role(self, admin_client: AsyncClient):
        """Test admin creating user with specific role."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': 'created@example.com',
                'name': 'Created User',
                'password': 'password123',
                'role': 'admin'
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'created@example.com'
        assert data['role'] == 'admin'

    async def test_admin_delete_user(self, async_client: AsyncClient, admin_client: AsyncClient):
        """Test admin deleting a user."""
        # Arrange: Create a user to delete
        create_response = await async_client.post(
            '/api/users',
            json={
                'email': 'todelete@example.com',
                'name': 'Delete Me',
                'password': 'password123'
            }
        )
        assert create_response.status_code == 201
        user_id = create_response.json()['id']

        # Act: Delete the user as admin
        response = await admin_client.delete(f'/api/users/{user_id}')

        # Assert
        assert response.status_code == 204

    async def test_admin_cannot_delete_self(
        self,
        admin_client: AsyncClient,
        user_repository
    ):
        """Test admin cannot delete own account."""
        admin_user = await user_repository.get_by_email('admin@test.example.com')
        assert admin_user is not None

        response = await admin_client.delete(f'/api/users/{admin_user.id}')

        assert response.status_code == 403
        data = response.json()
        assert data['detail'] in ('You cannot delete your own account', 'errors.user.cannot_delete_self')
    
    async def test_admin_delete_user_not_found(self, admin_client: AsyncClient):
        """Test deleting non-existent user returns 404."""
        response = await admin_client.delete('/api/users/nonexistent-user-id')

        assert response.status_code == 404
        data = response.json()
        assert 'status' in data or 'detail' in data
    
    async def test_list_users_pagination(self, async_client: AsyncClient, admin_client: AsyncClient):
        """Test user list pagination."""
        # Arrange: Create multiple users via API
        for i in range(5):
            await async_client.post(
                '/api/users',
                json={
                    'email': f'pagination{i}@example.com',
                    'name': f'User {i}',
                    'password': 'password123'
                }
            )

        # Act & Assert: Test pagination
        response = await admin_client.get('/api/users', params={'skip': 0, 'limit': 2})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 2

        response2 = await admin_client.get('/api/users', params={'skip': 2, 'limit': 2})
        assert response2.status_code == 200
        data2 = response2.json()
        assert isinstance(data2, list)
        assert len(data2) <= 2
    
    async def test_admin_create_user_duplicate_email(self, admin_client: AsyncClient, test_user):
        """Test admin creating user with duplicate email."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': test_user['email'],  # Duplicate
                'name': 'Duplicate User',
                'password': 'password123',
                'role': 'user'
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
    
    async def test_admin_create_user_invalid_role(self, admin_client: AsyncClient):
        """Test admin creating user with invalid role."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': 'newuser@example.com',
                'name': 'New User',
                'password': 'password123',
                'role': 'invalid_role'  # Invalid role
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data
