"""
Unit tests for models and schemas
Tests Pydantic models and data validation
"""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock, AsyncMock


def test_user_models():
    """Test user Pydantic models"""
    from app.schemas.user import UserCreate, UserLogin, UserResponse
    
    # Test UserCreate
    user_create = UserCreate(email="test@example.com", password="password123")
    assert user_create.email == "test@example.com"
    assert len(user_create.password) >= 6
    
    # Test UserLogin
    user_login = UserLogin(email="test@example.com", password="password123")
    assert user_login.email == "test@example.com"
    
    # Test UserResponse
    user_response = UserResponse(
        id="507f1f77bcf86cd799439011",
        email="test@example.com",
        created_at=datetime.utcnow(),
        is_active=True
    )
    assert user_response.is_active is True


def test_document_models():
    """Test document-related schemas"""
    from app.schemas.document import DocumentUpload, DocumentResponse, DocumentListResponse
    
    # Test DocumentUpload
    doc_upload = DocumentUpload(filename="test.pdf", content_type="application/pdf")
    assert doc_upload.filename == "test.pdf"
    assert doc_upload.content_type == "application/pdf"
    
    # Test DocumentResponse (with required fields)
    doc_response = DocumentResponse(
        id="123",
        filename="test.pdf",
        content_type="application/pdf", 
        file_size=1024,
        chunks_count=5,
        message="Success",
        created_at=datetime.utcnow()
    )
    assert doc_response.chunks_count == 5


def test_query_models():
    """Test query-related schemas"""
    from app.schemas.query import QuestionRequest, Token
    
    # Test QuestionRequest
    question = QuestionRequest(question="What is AI?")
    assert question.question == "What is AI?"
    
    # Test question length validation
    with pytest.raises(ValueError):
        QuestionRequest(question="")  # Too short
    
    # Test Token
    token = Token(access_token="test_token", token_type="bearer")
    assert token.access_token == "test_token"
    assert token.token_type == "bearer"


def test_model_field_validation():
    """Test model field validation rules"""
    from app.schemas.user import UserCreate
    from app.schemas.query import QuestionRequest
    
    # Test password length validation
    with pytest.raises(ValueError):
        UserCreate(email="test@example.com", password="123")  # Too short
    
    # Test email validation
    with pytest.raises(ValueError):
        UserCreate(email="invalid-email", password="password123")
    
    # Test question length limits
    with pytest.raises(ValueError):
        QuestionRequest(question="x" * 1001)  # Too long
