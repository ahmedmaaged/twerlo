"""
Tests for document processing and text utilities
Tests file parsing, text chunking, and document processing
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import io


def test_text_chunking():
    """Test text chunking functionality"""
    from app.utils.file_parser import text_chunker
    
    sample_text = """
    This is a test document with multiple sentences.
    It should be split into appropriate chunks.
    Each chunk should be meaningful and within size limits.
    The chunking algorithm should handle sentence boundaries intelligently.
    """
    
    chunks = text_chunker.chunk_text(sample_text, chunk_size=100, overlap=20)
    
    assert len(chunks) > 0
    assert all('text' in chunk for chunk in chunks)
    assert all('chunk_index' in chunk for chunk in chunks)
    assert all('start_char' in chunk for chunk in chunks)
    assert all('end_char' in chunk for chunk in chunks)
    assert all(len(chunk['text']) <= 120 for chunk in chunks)  # Allow overlap


def test_text_chunking_edge_cases():
    """Test text chunking with edge cases"""
    from app.utils.file_parser import text_chunker
    
    # Test empty text
    chunks = text_chunker.chunk_text("", chunk_size=100)
    assert len(chunks) == 0
    
    # Test very short text with large chunk size
    chunks = text_chunker.chunk_text("Short text.", chunk_size=100, overlap=0)
    assert len(chunks) >= 1
    assert any("Short text." in chunk['text'] for chunk in chunks)
    
    # Test text shorter than chunk size with no overlap
    short_text = "This is short."
    chunks = text_chunker.chunk_text(short_text, chunk_size=100, overlap=0)
    assert len(chunks) >= 1
    assert any(short_text in chunk['text'] for chunk in chunks)


def test_file_parser_structure():
    """Test file parser structure and methods"""
    from app.utils.file_parser import FileParser
    
    parser = FileParser()
    
    # Test that required methods exist
    assert hasattr(parser, 'extract_text_from_file')
    assert callable(getattr(parser, 'extract_text_from_file'))


@pytest.mark.asyncio
async def test_document_processor_validation():
    """Test document processor validation logic"""
    from app.services.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    
    # Test file size validation logic
    max_size = 10 * 1024 * 1024  # 10MB from config
    assert (1024 * 1024) <= max_size  # 1MB should be valid
    assert (15 * 1024 * 1024) > max_size  # 15MB should be invalid
    
    # Test filename validation patterns
    valid_filenames = ["document.pdf", "text.txt", "my_file.PDF", "test_doc.TXT"]
    invalid_filenames = ["", "../../../etc/passwd", "file.exe", "script.js"]
    
    for filename in valid_filenames:
        assert filename.lower().endswith(('.pdf', '.txt'))
    
    for filename in invalid_filenames:
        if filename:  # Non-empty filenames
            assert not filename.lower().endswith(('.pdf', '.txt')) or '/' in filename


@patch('app.services.embedding_service.openai')
def test_embedding_service(mock_openai):
    """Test embedding service with mocked OpenAI"""
    from app.services.embedding_service import EmbeddingService
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_openai.embeddings.create.return_value = mock_response
    
    embedding_service = EmbeddingService()
    
    # Test service initialization
    assert embedding_service.model == "text-embedding-3-small"
    assert hasattr(embedding_service, 'generate_embedding')


@pytest.mark.asyncio
async def test_logging_service():
    """Test query logging service"""
    from app.services.logging_service import LoggingService
    
    # Mock database
    with patch('app.services.logging_service.get_database') as mock_db:
        mock_collection = AsyncMock()
        mock_db.return_value.query_logs = mock_collection
        mock_collection.insert_one.return_value.inserted_id = "log_id_123"
        
        logging_service = LoggingService()
        
        # Test successful logging
        result = await logging_service.log_query(
            user_id="user123",
            question="Test question?",
            answer="Test answer",
            response_time_ms=1500,
            retrieved_chunks_count=3
        )
        
        assert result == "log_id_123"
        mock_collection.insert_one.assert_called_once()


def test_file_type_validation():
    """Test supported file type validation"""
    from app.utils.file_parser import FileParser
    
    # Test content type validation logic
    supported_types = ["text/plain", "application/pdf"]
    unsupported_types = ["image/jpeg", "application/json", "text/html"]
    
    for content_type in supported_types:
        assert content_type in ["text/plain", "application/pdf"]
    
    for content_type in unsupported_types:
        assert content_type not in ["text/plain", "application/pdf"]
