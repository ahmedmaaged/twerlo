from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]

class AnswerResponse(BaseModel):
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    response_time_ms: int

class QueryLogInDB(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    question: str
    answer: str
    response_time_ms: int
    retrieved_chunks_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
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

class QueryLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    question: str
    answer: str
    response_time_ms: int
    retrieved_chunks_count: int
    timestamp: datetime

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
