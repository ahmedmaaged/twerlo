from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[str] = Field(default=None, alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
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

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    is_active: bool
