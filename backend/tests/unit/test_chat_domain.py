import pytest

from src.models.domain import Chat, ChatMessage, ChatObserver


class RecordingObserver(ChatObserver):
    def __init__(self) -> None:
        self.received: list[ChatMessage] = []

    async def on_message(self, message: ChatMessage) -> None:
        self.received.append(message)


def make_chat(**kwargs) -> Chat:
    defaults = dict(participant_ids=["alice", "bob"], created_by="alice")
    return Chat(**{**defaults, **kwargs})


@pytest.mark.unit
@pytest.mark.asyncio
class TestChatDomainAddMessage:
    async def test_add_message_sets_participant_username(self):
        chat = make_chat(id="chat-1")
        msg = await chat.add_message("alice", "hello")
        assert msg.participant_username == "alice"

    async def test_add_message_sets_content(self):
        chat = make_chat(id="chat-1")
        msg = await chat.add_message("alice", "hello")
        assert msg.content == "hello"

    async def test_add_message_sets_chat_id(self):
        chat = make_chat(id="chat-42")
        msg = await chat.add_message("alice", "hi")
        assert msg.chat_id == "chat-42"

    async def test_add_message_chat_id_defaults_to_empty_when_no_id(self):
        chat = make_chat()
        msg = await chat.add_message("alice", "hi")
        assert msg.chat_id == ""

    async def test_add_message_generates_unique_ids(self):
        chat = make_chat()
        m1 = await chat.add_message("alice", "first")
        m2 = await chat.add_message("bob", "second")
        assert m1.id != m2.id

    async def test_add_message_appends_to_messages(self):
        chat = make_chat()
        await chat.add_message("alice", "first")
        await chat.add_message("bob", "second")
        assert len(chat.messages) == 2
        assert chat.messages[0].content == "first"
        assert chat.messages[1].content == "second"

    async def test_add_message_notifies_observers(self):
        observer = RecordingObserver()
        chat = make_chat()
        chat.add_observer(observer)
        msg = await chat.add_message("alice", "hi")
        assert len(observer.received) == 1
        assert observer.received[0].id == msg.id

    async def test_add_message_raises_for_non_participant(self):
        chat = make_chat()
        with pytest.raises(ValueError, match="not a participant"):
            await chat.add_message("eve", "intruder")

    async def test_add_message_multiple_observers_all_notified(self):
        o1, o2 = RecordingObserver(), RecordingObserver()
        chat = make_chat()
        chat.add_observer(o1)
        chat.add_observer(o2)
        await chat.add_message("alice", "ping")
        assert len(o1.received) == 1
        assert len(o2.received) == 1
