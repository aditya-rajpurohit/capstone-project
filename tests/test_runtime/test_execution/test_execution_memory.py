import uuid
from app.runtime.execution.execution_memory import ExecutionMemory


def test_execution_memory_initialization():
    memory = ExecutionMemory(
        user_query="show users",
        active_database_ids=["db1", "db2"],
        max_retries=2,
    )

    assert isinstance(uuid.UUID(memory.request_id), uuid.UUID)
    assert memory.user_query == "show users"
    assert memory.active_database_ids == ["db1", "db2"]
    assert memory.max_retries == 2
    assert memory.per_db_context == {}


def test_init_db_context():
    memory = ExecutionMemory("q", ["db1"], 2)

    memory.init_db_context("db1")

    assert memory.per_db_context["db1"]["retry_count"] == 0
    assert memory.per_db_context["db1"]["reflection_history"] == []


def test_increment_retry():
    memory = ExecutionMemory("q", ["db1"], 2)

    memory.init_db_context("db1")
    memory.increment_retry("db1")

    assert memory.per_db_context["db1"]["retry_count"] == 1


def test_add_reflection():
    memory = ExecutionMemory("q", ["db1"], 2)

    memory.init_db_context("db1")

    memory.add_reflection("db1", "SELECT 1", "syntax error")

    history = memory.per_db_context["db1"]["reflection_history"]

    assert len(history) == 1
    assert history[0]["previous_sql"] == "SELECT 1"
    assert history[0]["error_message"] == "syntax error"


def test_total_retry_count():
    memory = ExecutionMemory("q", ["db1", "db2"], 2)

    memory.init_db_context("db1")
    memory.init_db_context("db2")

    memory.increment_retry("db1")
    memory.increment_retry("db2")
    memory.increment_retry("db2")

    assert memory.total_retry_count() == 3


def test_set_db_error():
    memory = ExecutionMemory("q", ["db1"], 2)

    memory.set_db_error("db1", "connection failed")

    assert memory.per_db_context["db1"]["last_error_message"] == "connection failed"
