import pytest
from src.services.password import hash_password, verify_password


@pytest.mark.unit
class TestPasswordService:
    def test_hash_password(self):
        """Test that password hashing produces different outputs for same input."""
        password = 'testpassword123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != password
        assert hash1 != hash2  # Each hash should be unique due to salt
        assert len(hash1) > 0
    
    def test_verify_password_correct(self):
        """Test that correct password verification works."""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test that incorrect password verification fails."""
        password = 'testpassword123'
        wrong_password = 'wrongpassword'
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test that empty password verification fails."""
        password = 'testpassword123'
        hashed = hash_password(password)
        
        assert verify_password('', hashed) is False
