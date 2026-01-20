import pytest
from httpx import AsyncClient
from io import BytesIO
from PIL import Image


@pytest.mark.integration
class TestFileRoutes:
    def _create_test_image(self) -> bytes:
        """Create a small test image in memory."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    async def test_upload_avatar_success(self, authenticated_client: AsyncClient):
        """Test successful avatar upload using new flow."""
        image_data = self._create_test_image()
        
        # Step 1: Get upload URL
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'avatar.png', 'content_type': 'image/png', 'used_for': 'avatar'}
        )
        assert upload_url_response.status_code == 200
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        # Step 2: Upload file with used_for parameter
        upload_response = await authenticated_client.post(
            upload_url,
            files={'file': ('avatar.png', image_data, 'image/png')},
            params={'used_for': 'avatar'}
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data['file_key'] == file_key
        
        # Step 3: Set avatar using file_key
        avatar_response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        assert avatar_response.status_code == 200
        data = avatar_response.json()
        assert 'avatar_file_key' in data
        assert data['avatar_file_key'] == file_key
        assert 'avatar_url' in data
        assert data['avatar_url'] is not None
    
    async def test_upload_avatar_invalid_file_key(self, authenticated_client: AsyncClient):
        """Test avatar upload with non-existent file key."""
        response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': 'nonexistent/key/file.jpg'}
        )
        
        assert response.status_code == 404
    
    async def test_upload_avatar_unauthorized(self, async_client: AsyncClient):
        """Test avatar upload without authentication."""
        response = await async_client.post(
            '/api/users/me/avatar',
            json={'file_key': '550e8400-e29b-41d4-a716-446655440000/test.jpg'}
        )
        
        assert response.status_code == 401
    
    async def test_delete_avatar_success(self, authenticated_client: AsyncClient):
        """Test successful avatar deletion."""
        # First upload an avatar using new flow
        image_data = self._create_test_image()
        
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'avatar.png', 'content_type': 'image/png', 'used_for': 'avatar'}
        )
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        await authenticated_client.post(
            upload_url,
            files={'file': ('avatar.png', image_data, 'image/png')},
            params={'used_for': 'avatar'}
        )
        
        await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        # Then delete it
        response = await authenticated_client.delete('/api/users/me/avatar')
        
        assert response.status_code == 200
        data = response.json()
        assert data['avatar_file_key'] is None
        assert data['avatar_url'] is None
    
    async def test_get_file(self, authenticated_client: AsyncClient, test_user):
        """Test retrieving a file by key."""
        # Upload an avatar first using new flow
        image_data = self._create_test_image()
        
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'avatar.png', 'content_type': 'image/png', 'used_for': 'avatar'}
        )
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        await authenticated_client.post(
            upload_url,
            files={'file': ('avatar.png', image_data, 'image/png')},
            params={'used_for': 'avatar'}
        )
        
        await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        # Get the file
        response = await authenticated_client.get(f'/api/files/{file_key}')
        
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('image/')
        assert len(response.content) > 0
    
    async def test_get_file_different_content_types(self, authenticated_client: AsyncClient):
        """Test retrieving files with different content types."""
        # Test text file
        text_data = b'text file content'
        text_response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('test.txt', text_data, 'text/plain')}
        )
        text_key = text_response.json()['file_key']
        
        text_file_response = await authenticated_client.get(f'/api/files/{text_key}')
        assert text_file_response.status_code == 200
        assert 'text/plain' in text_file_response.headers['content-type']
        assert text_file_response.content == text_data
        
        # Test JSON file
        json_data = b'{"key": "value"}'
        json_response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('data.json', json_data, 'application/json')}
        )
        json_key = json_response.json()['file_key']
        
        json_file_response = await authenticated_client.get(f'/api/files/{json_key}')
        assert json_file_response.status_code == 200
        assert json_file_response.content == json_data
    
    async def test_unified_upload_endpoint(self, authenticated_client: AsyncClient):
        """Test unified file upload endpoint."""
        file_data = b'test file content'
        
        response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('test.txt', file_data, 'text/plain')}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'file_key' in data
        assert 'url' in data
        assert 'original_filename' in data
        assert data['original_filename'] == 'test.txt'
        # File key format: uuid/filename.ext (prefix is ignored)
        parts = data['file_key'].split('/')
        assert len(parts) == 2
        assert parts[1] == 'test.txt'
        # First part should be a UUID (36 chars with dashes)
        assert len(parts[0]) == 36
        assert parts[0].count('-') == 4
    
    async def test_upload_with_pregenerated_key(self, authenticated_client: AsyncClient):
        """Test upload with pre-generated file_key."""
        file_data = b'test file content with pregenerated key'
        
        # Step 1: Get upload URL to generate file_key
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'pregenerated.txt'}
        )
        upload_url_data = upload_url_response.json()
        pregenerated_key = upload_url_data['file_key']
        
        # Step 2: Upload with the pre-generated key
        response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('pregenerated.txt', file_data, 'text/plain')},
            params={'file_key': pregenerated_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['file_key'] == pregenerated_key
        assert data['original_filename'] == 'pregenerated.txt'
    
    async def test_upload_without_file_key(self, authenticated_client: AsyncClient):
        """Test upload without file_key (auto-generate)."""
        file_data = b'test file content auto-generated key'
        
        response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('autogen.txt', file_data, 'text/plain')}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'file_key' in data
        assert data['original_filename'] == 'autogen.txt'
        # Should have UUID format
        parts = data['file_key'].split('/')
        assert len(parts) == 2
        assert parts[1] == 'autogen.txt'
    
    async def test_upload_url_endpoint(self, authenticated_client: AsyncClient):
        """Test upload URL generation endpoint."""
        response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'photo.jpg', 'content_type': 'image/jpeg'}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'file_key' in data
        assert 'upload_url' in data
        assert 'method' in data
        assert data['method'] == 'POST'
        # File key format: uuid/filename.ext (prefix is ignored)
        assert data['file_key'].endswith('/photo.jpg')
        parts = data['file_key'].split('/')
        assert len(parts) == 2
        assert parts[1] == 'photo.jpg'
        # First part should be a UUID (36 chars with dashes)
        assert len(parts[0]) == 36
        assert parts[0].count('-') == 4
    
    async def test_get_file_not_found(self, authenticated_client: AsyncClient):
        """Test retrieving non-existent file."""
        response = await authenticated_client.get('/api/files/nonexistent_key')
        
        assert response.status_code == 404
    
    async def test_upload_url_unauthorized(self, async_client: AsyncClient):
        """Test upload URL endpoint requires authentication."""
        response = await async_client.get(
            '/api/files/upload-url',
            params={'filename': 'test.jpg'}
        )
        
        assert response.status_code == 401
    
    async def test_upload_unauthorized(self, async_client: AsyncClient):
        """Test upload endpoint requires authentication."""
        file_data = b'test content'
        
        response = await async_client.post(
            '/api/files/upload',
            files={'file': ('test.txt', file_data, 'text/plain')}
        )
        
        assert response.status_code == 401
    
    async def test_upload_file_too_large(self, authenticated_client: AsyncClient):
        """Test file size validation."""
        large_file_data = b'x' * (11 * 1024 * 1024)  # 11MB
        
        response = await authenticated_client.post(
            '/api/files/upload',
            files={'file': ('large.txt', large_file_data, 'text/plain')}
        )
        
        assert response.status_code == 400
    
    async def test_avatar_file_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test avatar endpoint returns 404 when file_key doesn't point to existing file."""
        # Try to set non-existent file as avatar
        response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': 'nonexistent-uuid/nonexistent.png'}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert 'status' in data or 'detail' in data
    
    async def test_avatar_invalid_file_type(self, authenticated_client: AsyncClient):
        """Test avatar must be an image file."""
        # Upload a non-image file
        file_data = b'not an image'
        
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'test.txt'}
        )
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        await authenticated_client.post(
            upload_url,
            files={'file': ('test.txt', file_data, 'text/plain')}
        )
        
        # Try to set it as avatar (should fail)
        response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        assert response.status_code == 400
    
    async def test_avatar_used_for_validation(self, authenticated_client: AsyncClient):
        """Test avatar endpoint validates used_for field."""
        # Upload a file marked for document use, not avatar
        image_data = self._create_test_image()
        
        upload_url_response = await authenticated_client.get(
            '/api/files/upload-url',
            params={'filename': 'document.png', 'content_type': 'image/png', 'used_for': 'document'}
        )
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        await authenticated_client.post(
            upload_url,
            files={'file': ('document.png', image_data, 'image/png')},
            params={'used_for': 'document'}
        )
        
        # Try to set it as avatar (should fail because used_for != 'avatar')
        response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'status' in data or 'detail' in data
    
    async def test_avatar_ownership_validation(self, async_client: AsyncClient, authenticated_client: AsyncClient):
        """Test avatar endpoint validates file ownership."""
        # Arrange: Create another user via API and upload file as that user
        create_response = await async_client.post(
            '/api/users',
            json={
                'email': 'other@example.com',
                'name': 'Other User',
                'password': 'password123'
            }
        )
        assert create_response.status_code == 201
        
        # Login as other user to get token
        login_response = await async_client.post(
            '/api/auth/login',
            json={
                'email': 'other@example.com',
                'password': 'password123',
                'strategy': 'credentials'
            }
        )
        assert login_response.status_code == 200
        other_token = login_response.json()['access_token']
        
        # Upload a file as the other user
        image_data = self._create_test_image()
        
        # Save the original token from authenticated_client
        original_auth = authenticated_client.headers.get('Authorization')
        
        # Temporarily use other user's token for upload
        async_client.headers.update({'Authorization': f'Bearer {other_token}'})
        
        upload_url_response = await async_client.get(
            '/api/files/upload-url',
            params={'filename': 'avatar.png', 'content_type': 'image/png', 'used_for': 'avatar'}
        )
        upload_url_data = upload_url_response.json()
        file_key = upload_url_data['file_key']
        upload_url = upload_url_data['upload_url']
        
        await async_client.post(
            upload_url,
            files={'file': ('avatar.png', image_data, 'image/png')},
            params={'used_for': 'avatar'}
        )
        
        # Restore original user's token for authenticated_client
        if original_auth:
            authenticated_client.headers.update({'Authorization': original_auth})
        else:
            authenticated_client.headers.pop('Authorization', None)
        
        # Act: Try to set other user's file as avatar as original user (should fail)
        response = await authenticated_client.post(
            '/api/users/me/avatar',
            json={'file_key': file_key}
        )
        
        # Assert
        assert response.status_code == 403
        data = response.json()
        assert 'status' in data or 'detail' in data
        
        # Clean up
        async_client.headers.pop('Authorization', None)