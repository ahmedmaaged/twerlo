from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.schemas.query import RetrievedChunk

class DocumentUpload(BaseModel):
    filename: str
    content_type: str

class DocumentChunk(BaseModel):
    text: str
    chunk_index: int
    start_char: int
    end_char: int

class DocumentInDB(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    filename: str
    content_type: str
    file_size: int
    original_text: str
    chunks_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return None
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            return v
        raise ValueError('Invalid ObjectId')

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    filename: str
    content_type: str
    file_size: int
    chunks_count: int
    created_at: datetime

class DocumentListResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int
    chunks_count: int
    created_at: str

class DeleteResponse(BaseModel):
    message: str
    deleted_document_id: str


class TestRetrievalRequest(BaseModel):
    query: str
    score_threshold: Optional[float] = 0.01
    limit: Optional[int] = 10

class TestRetrievalResponse(BaseModel):
    query: str
    embedding_preview: List[float]  
    chunks_found: int
    retrieved_chunks: List[RetrievedChunk]
    score_threshold_used: float