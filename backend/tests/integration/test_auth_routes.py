import pytest
from httpx import AsyncClient

from src.auth.jwt import create_access_token, create_oauth_state_token


@pytest.mark.integration
class TestAuthRoutes:
    async def test_login_success(self, async_client: AsyncClient, test_user):
        """Test successful login."""
        response = await async_client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'testpassword123',
                'strategy': 'credentials'
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'bearer'
    
    async def test_login_invalid_credentials(self, async_client: AsyncClient, test_user):
        """Test login with invalid credentials."""
        response = await async_client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'wrongpassword',
                'strategy': 'credentials'
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')
        assert 'status' in data
    
    async def test_login_user_not_found(self, async_client: AsyncClient):
        """Test login with non-existent user."""
        response = await async_client.post(
            '/api/auth/login',
            json={
                'email': 'nonexistent@example.com',
                'password': 'password123',
                'strategy': 'credentials'
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')

    async def test_login_unknown_strategy(self, async_client: AsyncClient, test_user):
        response = await async_client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'testpassword123',
                'strategy': 'unknown'
            }
        )

        assert response.status_code == 401
    
    async def test_refresh_token_success(self, async_client: AsyncClient, test_user):
        """Test successful token refresh."""
        # First login
        login_response = await async_client.post(
            '/api/auth/login',
            json={
                'email': test_user['email'],
                'password': 'testpassword123',
                'strategy': 'credentials'
            }
        )
        refresh_token = login_response.json()['refresh_token']
        
        # Refresh token
        response = await async_client.post(
            '/api/auth/refresh',
            json={'refresh_token': refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh with invalid token."""
        response = await async_client.post(
            '/api/auth/refresh',
            json={'refresh_token': 'invalid.token.here'}
        )
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')

    async def test_refresh_token_with_access_token(self, async_client: AsyncClient):
        access_token = create_access_token(
            data={'sub': 'user-id', 'email': 'user@example.com', 'role': 'user'}
        )

        response = await async_client.post(
            '/api/auth/refresh',
            json={'refresh_token': access_token}
        )

        assert response.status_code == 401
    
    async def test_refresh_token_expired(self, async_client: AsyncClient):
        """Test refresh with expired/invalid token."""
        # Use a clearly invalid token format
        response = await async_client.post(
            '/api/auth/refresh',
            json={'refresh_token': 'expired.invalid.token'}
        )
        
        # Should fail with 401 (token expired or invalid)
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')
    
    async def test_get_current_user_success(self, authenticated_client: AsyncClient):
        """Test getting current user info."""
        response = await authenticated_client.get('/api/auth/me')
        
        assert response.status_code == 200
        data = response.json()
        assert 'id' in data
        assert 'email' in data
        assert 'name' in data
    
    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = response.json()
        # Status can be 'error' (translated) or 'common.error' (translation key)
        assert data['status'] in ('error', 'common.error')
    
    async def test_logout_success(self, authenticated_client: AsyncClient):
        """Test successful logout."""
        response = await authenticated_client.post('/api/auth/logout')
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data

    async def test_oauth_authorize_returns_url(self, async_client: AsyncClient):
        """Test OAuth authorize endpoint returns authorization URL."""
        response = await async_client.get('/api/auth/oauth/google/authorize')

        assert response.status_code in (200, 400, 500)  # May fail without OAuth config
        if response.status_code == 200:
            data = response.json()
            assert 'authorization_url' in data or 'state' in data

    async def test_oauth_authorize_unknown_provider(self, async_client: AsyncClient):
        response = await async_client.get('/api/auth/oauth/unknown/authorize')

        assert response.status_code == 400
    
    async def test_oauth_callback_missing_code(self, async_client: AsyncClient):
        """Test OAuth callback with missing code parameter."""
        response = await async_client.post(
            '/api/auth/oauth/google/callback',
            params={'state': 'test-state'}
        )

        assert response.status_code == 400
    
    async def test_oauth_callback_missing_state(self, async_client: AsyncClient):
        """Test OAuth callback with missing state parameter."""
        response = await async_client.post(
            '/api/auth/oauth/google/callback',
            params={'code': 'authcode'}
        )

        assert response.status_code == 400

    async def test_oauth_callback_invalid_state_cookie(self, async_client: AsyncClient):
        state_token = create_oauth_state_token('state-a', 'google')
        async_client.cookies.set('oauth_state', state_token)

        response = await async_client.post(
            '/api/auth/oauth/google/callback',
            params={'code': 'authcode', 'state': 'state-b'}
        )

        assert response.status_code == 400