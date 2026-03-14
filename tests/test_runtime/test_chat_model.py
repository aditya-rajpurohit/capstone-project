from app.runtime.chat_model import ChatSessionModel


def test_chat_session_model_creation():
    session = ChatSessionModel(
        session_id="test-session",
        summary="Test summary",
        turns=[{"role": "user", "content": "hello"}],
    )

    assert session.session_id == "test-session"
    assert session.summary == "Test summary"
    assert session.turns == [{"role": "user", "content": "hello"}]


def test_chat_session_model_defaults():
    session = ChatSessionModel(
        session_id="test-session",
        turns=[]
    )

    # DB defaults are not populated until insert
    assert session.id is None
    assert session.created_at is None
    assert session.updated_at is None

    assert session.turns == []
