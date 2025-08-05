"""
Shared pytest fixtures and configuration for Twerlo tests
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_user():
    """Sample user data for testing"""
    return {
        "id": "507f1f77bcf86cd799439011",
        "email": "test@example.com",
        "password": "securepassword123",
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def sample_document():
    """Sample document data for testing"""
    return {
        "id": "507f1f77bcf86cd799439012", 
        "filename": "test_document.txt",
        "content_type": "text/plain",
        "file_size": 1024,
        "chunks_count": 3,
        "user_id": "507f1f77bcf86cd799439011",
        "original_text": "This is a sample document content for testing purposes.",
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def auth_token(sample_user):
    """Generate a valid JWT token for testing"""
    from app.utils.security import create_access_token
    
    token = create_access_token(data={"sub": sample_user["email"]})
    return token

@pytest.fixture
def auth_headers(auth_token):
    """HTTP headers with authentication for API testing"""
    return {"Authorization": f"Bearer {auth_token}"}

# Test markers for categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.api = pytest.mark.api
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
