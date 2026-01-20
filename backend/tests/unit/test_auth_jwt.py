import pytest
from datetime import timedelta
from src.auth.jwt import create_access_token, create_refresh_token, verify_token, decode_token


@pytest.mark.unit
class TestJWT:
    def test_create_access_token(self):
        """Test that access token is created successfully."""
        data = {'sub': 'user123', 'email': 'test@example.com'}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test that refresh token is created successfully."""
        data = {'sub': 'user123', 'email': 'test@example.com'}
        token = create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_valid(self):
        """Test that valid token verification works."""
        data = {'sub': 'user123', 'email': 'test@example.com'}
        token = create_access_token(data)
        
        payload = verify_token(token)
        
        assert payload is not None
        assert payload['sub'] == 'user123'
        assert payload['email'] == 'test@example.com'
    
    def test_verify_token_invalid(self):
        """Test that invalid token verification returns None."""
        invalid_token = 'invalid.token.here'
        
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    def test_refresh_token_has_type(self):
        """Test that refresh token has type field."""
        data = {'sub': 'user123', 'email': 'test@example.com'}
        token = create_refresh_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.get('type') == 'refresh'
    
    def test_access_token_expires(self):
        """Test that access token has expiration."""
        data = {'sub': 'user123', 'email': 'test@example.com'}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = verify_token(token)
        
        assert payload is None  # Expired token should return None
