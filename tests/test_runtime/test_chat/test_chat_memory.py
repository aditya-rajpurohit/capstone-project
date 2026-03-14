from app.runtime.chat.chat_memory import ChatMemory


def test_add_turn():
    mem = ChatMemory("session1")

    mem.add_turn("user", "hello")

    assert len(mem.turns) == 1
    assert mem.turns[0]["role"] == "user"
    assert mem.turns[0]["content"] == "hello"


def test_get_recent_turns():
    mem = ChatMemory("s")

    for i in range(5):
        mem.add_turn("user", f"msg{i}")

    recent = mem.get_recent_turns(2)

    assert len(recent) == 2
    assert recent[-1]["content"] == "msg4"


def test_needs_summarization():
    mem = ChatMemory("s", max_turns=2)

    mem.add_turn("user", "a")
    mem.add_turn("user", "b")
    mem.add_turn("user", "c")

    assert mem.needs_summarization() is True


def test_apply_summary():
    mem = ChatMemory("s", keep_recent=2)

    for i in range(5):
        mem.add_turn("user", f"msg{i}")

    mem.apply_summary("summary")

    assert mem.summary == "summary"
    assert len(mem.turns) == 2


def test_query_memory_store_and_get():
    mem = ChatMemory("s")

    mem.store_query_result("db1", "SELECT 1", {"rows": []})

    result = mem.get_query_result("db1", "SELECT 1")

    assert result == {"rows": []}
