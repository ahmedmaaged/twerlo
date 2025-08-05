"""
Tests for application configuration and settings
Tests config loading, environment variables, and default values
"""

import pytest
from unittest.mock import patch


def test_configuration_loading():
    """Test application configuration"""
    from app.config import settings
    
    # Test that required settings exist
    required_settings = [
        'jwt_secret_key', 'jwt_algorithm', 'access_token_expire_minutes',
        'mongodb_url', 'database_name', 'qdrant_url',
        'app_host', 'app_port', 'max_file_size_mb'
    ]
    
    for setting in required_settings:
        assert hasattr(settings, setting), f"Missing required setting: {setting}"


def test_default_values():
    """Test default configuration values"""
    from app.config import settings
    
    # Test default values
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.max_file_size_mb == 10
    assert settings.app_port == 8000


def test_database_configuration():
    """Test database-related configuration"""
    from app.config import settings
    
    # Test MongoDB settings
    assert hasattr(settings, 'mongodb_url')
    assert hasattr(settings, 'database_name')
    assert settings.database_name == "twerlo_db"
    
    # Test Qdrant settings
    assert hasattr(settings, 'qdrant_url')
    assert hasattr(settings, 'qdrant_collection_name')
    assert settings.qdrant_collection_name == "documents"


def test_security_configuration():
    """Test security-related configuration"""
    from app.config import settings
    
    # Test JWT settings
    assert hasattr(settings, 'jwt_secret_key')
    assert hasattr(settings, 'jwt_algorithm')
    assert hasattr(settings, 'access_token_expire_minutes')
    
    # Test that JWT algorithm is secure
    assert settings.jwt_algorithm in ["HS256", "RS256", "ES256"]


def test_application_limits():
    """Test application limit configurations"""
    from app.config import settings
    
    # Test file size limits
    assert settings.max_file_size_mb > 0
    assert settings.max_file_size_mb <= 100  # Reasonable upper limit
    
    # Test token expiration
    assert settings.access_token_expire_minutes > 0
    assert settings.access_token_expire_minutes <= 1440  # Max 24 hours


def test_environment_variable_support():
    """Test that environment variables are supported"""
    from app.config import Settings
    
    # Test that the Settings class uses BaseSettings
    from pydantic_settings import BaseSettings
    assert issubclass(Settings, BaseSettings)
    
    # Test that Config class exists for .env file support
    settings = Settings()
    assert hasattr(settings, 'model_config') or hasattr(settings.__class__, 'Config')
