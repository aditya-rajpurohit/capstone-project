import pytest
from unittest.mock import AsyncMock
from app.runtime.chat.chat_summarizer import ChatSummarizer


@pytest.mark.asyncio
async def test_chat_summarizer_calls_model():
    mock_model = AsyncMock()
    mock_model.generate.return_value = "summary text"

    summarizer = ChatSummarizer(mock_model)

    turns = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]

    result = await summarizer.summarize(turns)

    mock_model.generate.assert_awaited_once()
    assert result == "summary text"
