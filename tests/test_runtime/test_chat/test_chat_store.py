import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.runtime.chat.chat_store import ChatStore
from app.runtime.chat.chat_memory import ChatMemory


@pytest.mark.asyncio
async def test_load_returns_empty_memory_if_not_found():
    store = ChatStore()

    session = AsyncMock()
    session.scalar.return_value = None

    SessionMock = MagicMock()
    SessionMock.return_value.__aenter__.return_value = session

    with patch("app.runtime.chat.chat_store.get_async_session", return_value=SessionMock):

        mem = await store.load("s1")

    assert mem.session_id == "s1"
    assert mem.turns == []


@pytest.mark.asyncio
async def test_save_creates_new_row():
    store = ChatStore()
    mem = ChatMemory("s1")
    mem.turns = [{"role": "user", "content": "hi"}]

    session = AsyncMock()
    session.scalar.return_value = None

    SessionMock = MagicMock()
    SessionMock.return_value.__aenter__.return_value = session

    with patch("app.runtime.chat.chat_store.get_async_session", return_value=SessionMock):

        await store.save(mem)

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
