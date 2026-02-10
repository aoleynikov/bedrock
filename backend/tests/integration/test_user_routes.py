import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestUserRoutes:
    async def test_create_user_success(self, client: AsyncClient, user_payload: dict):
        """Test successful user creation."""
        response = await client.post(
            '/api/users',
            json={
                'email': user_payload['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['email'] == user_payload['email']
        assert data['name'] == user_payload['name']
        assert 'id' in data
        assert 'password' not in data
        assert 'hashed_password' not in data

    async def test_create_user_duplicate_email(
        self, client: AsyncClient, test_user: dict, user_payload: dict
    ):
        """Test user creation with duplicate email."""
        response = await client.post(
            '/api/users',
            json={
                'email': test_user['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data

    async def test_create_user_invalid_email(self, client: AsyncClient, user_payload: dict):
        """Test user creation with invalid email."""
        response = await client.post(
            '/api/users',
            json={
                'email': 'invalid-email',
                'name': user_payload['name'],
                'password': user_payload['password'],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data

    async def test_create_user_short_password(self, client: AsyncClient, user_payload: dict):
        """Test user creation with password too short."""
        response = await client.post(
            '/api/users',
            json={
                'email': user_payload['email'],
                'name': user_payload['name'],
                'password': 'short',
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data

    async def test_list_users_unauthenticated(self, client: AsyncClient):
        """Test listing users without authentication."""
        response = await client.get('/api/users')
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_list_users_forbidden_for_regular_user(
        self, authenticated_client: AsyncClient, test_user: dict
    ):
        """Test listing users as regular user (should be forbidden)."""
        response = await authenticated_client.get('/api/users')
        assert response.status_code == 403
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_list_users_admin(self, client: AsyncClient, admin_client: AsyncClient):
        """Test listing users as admin."""
        response = await admin_client.get('/api/users')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_admin_create_user_with_role(
        self, admin_client: AsyncClient, user_payload: dict
    ):
        """Test admin creating user with specific role."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': user_payload['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
                'role': 'admin',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data['email'] == user_payload['email']
        assert data['role'] == 'admin'

    async def test_admin_delete_user(
        self, client: AsyncClient, admin_client: AsyncClient, user_payload: dict
    ):
        """Test admin deleting a user."""
        create_response = await client.post(
            '/api/users',
            json={
                'email': user_payload['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
            },
        )
        assert create_response.status_code == 201
        user_id = create_response.json()['id']
        response = await admin_client.delete(f'/api/users/{user_id}')
        assert response.status_code == 204

    async def test_admin_cannot_delete_self(
        self, admin_client: AsyncClient, admin_user: dict
    ):
        """Test admin cannot delete own account."""
        response = await admin_client.delete(f'/api/users/{admin_user["id"]}')
        assert response.status_code == 403
        data = response.json()
        assert data['detail'] in (
            'You cannot delete your own account',
            'errors.user.cannot_delete_self',
        )

    async def test_admin_delete_user_not_found(self, admin_client: AsyncClient):
        """Test deleting non-existent user returns 404."""
        response = await admin_client.delete('/api/users/nonexistent-user-id')
        assert response.status_code == 404
        data = response.json()
        assert 'status' in data or 'detail' in data

    async def test_list_users_pagination(
        self, client: AsyncClient, admin_client: AsyncClient, five_user_payloads: list
    ):
        """Test user list pagination."""
        for payload in five_user_payloads:
            await client.post(
                '/api/users',
                json={
                    'email': payload['email'],
                    'name': payload['name'],
                    'password': payload['password'],
                },
            )
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

    async def test_admin_create_user_duplicate_email(
        self, admin_client: AsyncClient, test_user: dict, user_payload: dict
    ):
        """Test admin creating user with duplicate email."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': test_user['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
                'role': 'user',
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data

    async def test_admin_create_user_invalid_role(
        self, admin_client: AsyncClient, user_payload: dict
    ):
        """Test admin creating user with invalid role."""
        response = await admin_client.post(
            '/api/users/admin',
            json={
                'email': user_payload['email'],
                'name': user_payload['name'],
                'password': user_payload['password'],
                'role': 'invalid_role',
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
        assert 'errors' in data
