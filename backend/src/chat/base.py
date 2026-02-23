from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import uuid4

from src.models.domain import ChatMessage


class Chat(ABC):
    def __init__(self) -> None:
        self._messages: list[ChatMessage] = []

    async def list_messages(self) -> list[ChatMessage]:
        return list(self._messages)

    async def post_message(self, content: str, participant_username: str) -> ChatMessage:
        message = ChatMessage(
            id=uuid4().hex,
            content=content,
            participant_username=participant_username,
            created_at=datetime.now(timezone.utc),
        )
        self._messages.append(message)
        await self.on_message(message)
        return message

    async def delete_message(self, message_id: str) -> bool:
        initial_len = len(self._messages)
        self._messages = [m for m in self._messages if m.id != message_id]
        return len(self._messages) < initial_len

    @abstractmethod
    async def on_message(self, message: ChatMessage) -> None:
        pass
