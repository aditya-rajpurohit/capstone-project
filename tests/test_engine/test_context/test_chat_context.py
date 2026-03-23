from app.engine.context.chat_context import ChatContext


def test_chat_context_initialization():
    ctx = ChatContext(active_database_ids=["db1", "db2"])

    assert ctx.active_database_ids == ["db1", "db2"]
