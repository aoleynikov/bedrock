from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PrivateAttr, field_validator
from pydantic_core import PydanticCustomError


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


class ChatMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chat_id: str
    user_id: str
    content: str
    created_at: datetime


class ChatObserver(ABC):
    @abstractmethod
    async def on_message(self, message: ChatMessage) -> None: ...


class Chat(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: Optional[str] = None
    participant_ids: list[str]
    created_by: str
    messages: list[ChatMessage] = []
    created_at: Optional[datetime] = None

    _observers: list[ChatObserver] = PrivateAttr(default_factory=list)

    def add_observer(self, observer: ChatObserver) -> None:
        self._observers.append(observer)

    async def add_message(self, user_id: str, content: str) -> ChatMessage:
        if user_id not in self.participant_ids:
            raise ValueError(f"User '{user_id}' is not a participant in this chat")
        message = ChatMessage(
            id=str(uuid4()),
            chat_id=self.id or "",
            user_id=user_id,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self.messages.append(message)
        for observer in self._observers:
            await observer.on_message(message)
        return message
