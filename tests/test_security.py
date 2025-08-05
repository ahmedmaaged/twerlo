"""
Tests for security and authentication utilities
Tests JWT tokens, password hashing, and auth functions
"""

import pytest
from datetime import timedelta
from unittest.mock import patch, Mock, AsyncMock


def test_password_hashing():
    """Test password hashing and verification"""
    from app.utils.security import get_password_hash, verify_password
    
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert len(hashed) > 20
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_operations():
    """Test JWT token creation and verification"""
    from app.utils.security import create_access_token, verify_token
    
    # Test token creation
    token = create_access_token(
        data={"sub": "test@example.com"}, 
        expires_delta=timedelta(minutes=30)
    )
    
    assert isinstance(token, str)
    assert len(token) > 50
    
    # Test token verification
    email = verify_token(token)
    assert email == "test@example.com"


def test_invalid_token_handling():
    """Test handling of invalid tokens"""
    from app.utils.security import verify_token
    
    # Test invalid token
    invalid_token = "invalid.jwt.token"
    email = verify_token(invalid_token)
    assert email is None
    
    # Test expired token (would need to mock time)
    # This is covered by integration tests


@pytest.mark.asyncio
async def test_auth_service():
    """Test authentication service with mocked database"""
    from app.services.auth import AuthService
    from app.schemas.user import UserCreate
    
    auth_service = AuthService()
    
    # Mock database operations
    with patch('app.services.auth.get_database') as mock_db:
        mock_collection = AsyncMock()
        mock_db.return_value.users = mock_collection
        
        # Test user creation setup
        mock_collection.find_one.return_value = None  # User doesn't exist
        mock_collection.insert_one.return_value.inserted_id = "user_id_123"
        
        user_data = UserCreate(email="test@example.com", password="password123")
        result = await auth_service.create_user(user_data)
        
        assert result.email == "test@example.com"
        mock_collection.insert_one.assert_called_once()


def test_security_configuration():
    """Test security-related configuration"""
    from app.config import settings
    
    # Test that security settings exist
    assert hasattr(settings, 'jwt_secret_key')
    assert hasattr(settings, 'jwt_algorithm')
    assert hasattr(settings, 'access_token_expire_minutes')
    
    # Test default values
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
