from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic_core import PydanticCustomError
from typing import Optional, Literal
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise PydanticCustomError('password_min_length', 'Password too short')
        return v


class AdminUserCreate(UserCreate):
    role: Literal['user', 'admin'] = 'user'


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    hashed_password: str
    avatar_file_key: Optional[str] = None
    role: Literal['user', 'admin'] = 'user'
    created_at: Optional[datetime] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    avatar_file_key: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Literal['user', 'admin'] = 'user'
    created_at: Optional[datetime] = None


class UploadedFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    file_key: str
    owner_id: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: int
    used_for: Optional[str] = None
    created_at: Optional[datetime] = None
