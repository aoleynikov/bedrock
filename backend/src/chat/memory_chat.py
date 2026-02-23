from src.chat.base import Chat
from src.models.domain import ChatMessage


class MemoryChat(Chat):
    async def on_message(self, message: ChatMessage) -> None:
        pass
