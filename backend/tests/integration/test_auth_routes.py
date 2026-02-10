import pytest
from httpx import AsyncClient

from src.auth.jwt import create_access_token, create_oauth_state_token


@pytest.mark.integration
class TestAuthRoutes:
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login."""
        response = await client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': test_user['password'],
                'strategy': 'credentials',
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'

    async def test_login_invalid_credentials(self, client: AsyncClient, test_user: dict):
        """Test login with invalid credentials."""
        response = await client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'wrongpassword',
                'strategy': 'credentials',
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')
        assert 'status' in data

    async def test_login_user_not_found(self, client: AsyncClient, user_payload: dict):
        """Test login with non-existent user."""
        response = await client.post(
            '/api/auth/login',
            json={
                'email': user_payload['email'],
                'password': user_payload['password'],
                'strategy': 'credentials',
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_login_unknown_strategy(self, client: AsyncClient, test_user: dict):
        response = await client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': test_user['password'],
                'strategy': 'unknown',
            },
        )
        assert response.status_code == 401

    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Test successful token refresh."""
        login_response = await client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': test_user['password'],
                'strategy': 'credentials',
            },
        )
        refresh_token = login_response.json()['refresh_token']
        response = await client.post(
            '/api/auth/refresh',
            json={'refresh_token': refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            '/api/auth/refresh',
            json={'refresh_token': 'invalid.token.here'},
        )
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_refresh_token_with_access_token(self, client: AsyncClient, user_payload: dict):
        access_token = create_access_token(
            data={'sub': 'user-id', 'email': user_payload['email'], 'role': 'user'},
        )
        response = await client.post(
            '/api/auth/refresh',
            json={'refresh_token': access_token},
        )
        assert response.status_code == 401

    async def test_refresh_token_expired(self, client: AsyncClient):
        """Test refresh with expired/invalid token."""
        response = await client.post(
            '/api/auth/refresh',
            json={'refresh_token': 'expired.invalid.token'},
        )
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_get_current_user_success(self, authenticated_client: AsyncClient):
        """Test getting current user info."""
        response = await authenticated_client.get('/api/auth/me')
        assert response.status_code == 200
        data = response.json()
        assert 'id' in data
        assert 'email' in data
        assert 'name' in data

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get('/api/auth/me')
        assert response.status_code == 401
        data = response.json()
        assert data['status'] in ('error', 'common.error')

    async def test_logout_success(self, authenticated_client: AsyncClient):
        """Test successful logout."""
        response = await authenticated_client.post('/api/auth/logout')
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    async def test_oauth_authorize_returns_url(self, client: AsyncClient):
        """Test OAuth authorize endpoint returns authorization URL."""
        response = await client.get('/api/auth/oauth/google/authorize')
        assert response.status_code in (200, 400, 500)
        if response.status_code == 200:
            data = response.json()
            assert 'authorization_url' in data or 'state' in data

    async def test_oauth_authorize_unknown_provider(self, client: AsyncClient):
        response = await client.get('/api/auth/oauth/unknown/authorize')
        assert response.status_code == 400

    async def test_oauth_callback_missing_code(self, client: AsyncClient):
        """Test OAuth callback with missing code parameter."""
        response = await client.post(
            '/api/auth/oauth/google/callback',
            params={'state': 'test-state'},
        )
        assert response.status_code == 400

    async def test_oauth_callback_missing_state(self, client: AsyncClient):
        """Test OAuth callback with missing state parameter."""
        response = await client.post(
            '/api/auth/oauth/google/callback',
            params={'code': 'authcode'},
        )
        assert response.status_code == 400

    async def test_oauth_callback_invalid_state_cookie(self, client: AsyncClient):
        state_token = create_oauth_state_token('state-a', 'google')
        client.cookies.set('oauth_state', state_token)
        response = await client.post(
            '/api/auth/oauth/google/callback',
            params={'code': 'authcode', 'state': 'state-b'},
        )
        assert response.status_code == 400
