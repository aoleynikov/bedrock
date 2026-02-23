import pytest

from src.chat.base import Chat
from src.chat.memory_chat import MemoryChat
from src.models.domain import ChatMessage


class RecordingChat(Chat):
    def __init__(self) -> None:
        super().__init__()
        self.received: list[ChatMessage] = []

    async def on_message(self, message: ChatMessage) -> None:
        self.received.append(message)


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatBase:
    async def test_post_message_adds_to_list_and_calls_on_message(self):
        chat = RecordingChat()
        msg = await chat.post_message('hello', 'alice')
        assert msg.content == 'hello'
        assert msg.participant_username == 'alice'
        assert msg.id
        assert msg.created_at
        listed = await chat.list_messages()
        assert len(listed) == 1
        assert listed[0].id == msg.id
        assert len(chat.received) == 1
        assert chat.received[0].id == msg.id
        assert chat.received[0].content == 'hello'
        assert chat.received[0].participant_username == 'alice'

    async def test_list_messages_returns_in_order(self):
        chat = MemoryChat()
        await chat.post_message('first', 'alice')
        await chat.post_message('second', 'bob')
        listed = await chat.list_messages()
        assert len(listed) == 2
        assert listed[0].content == 'first'
        assert listed[1].content == 'second'

    async def test_delete_message_removes_by_id_returns_true(self):
        chat = MemoryChat()
        msg = await chat.post_message('to delete', 'alice')
        deleted = await chat.delete_message(msg.id)
        assert deleted is True
        listed = await chat.list_messages()
        assert len(listed) == 0

    async def test_delete_message_returns_false_when_id_missing(self):
        chat = MemoryChat()
        await chat.post_message('keep', 'alice')
        deleted = await chat.delete_message('nonexistent-id')
        assert deleted is False
        listed = await chat.list_messages()
        assert len(listed) == 1

    async def test_memory_chat_end_to_end_post_list_delete(self):
        chat = MemoryChat()
        m1 = await chat.post_message('a', 'alice')
        m2 = await chat.post_message('b', 'bob')
        assert len(await chat.list_messages()) == 2
        await chat.delete_message(m1.id)
        listed = await chat.list_messages()
        assert len(listed) == 1
        assert listed[0].id == m2.id
        assert listed[0].content == 'b'
