from unittest.mock import patch

from app.core.constants import MAX_REFLECTION_RETRIES
from app.engine.context.context_builder import ContextBuilder
from app.runtime.execution.execution_memory import ExecutionMemory


def test_build_for_planner():
    memory = ExecutionMemory(
        user_query="Show users",
        active_database_ids=[],
        max_retries=MAX_REFLECTION_RETRIES,
    )

    ctx = ContextBuilder.build_for_planner(memory)

    assert ctx.user_query == "Show users"


def test_build_for_query():
    memory = ExecutionMemory(
        user_query="Show users",
        active_database_ids=[],
        max_retries=MAX_REFLECTION_RETRIES,
    )

    memory.planner_output = {"intent": "select"}
    memory.trace_hits = []
    memory.schema_hits = []

    schema = {"tables": [{"name": "users"}]}

    with patch(
        "app.engine.context.context_builder.SchemaSelector.select",
        return_value=schema,
    ):
        ctx = ContextBuilder.build_for_query(memory, "db1", schema)

    assert ctx.user_query == "Show users"
    assert ctx.plan == {"intent": "select"}
    assert ctx.filtered_schema == schema


def test_build_for_reflection():
    memory = ExecutionMemory(
        user_query="Show users",
        active_database_ids=[],
        max_retries=MAX_REFLECTION_RETRIES,
    )

    memory.planner_output = {"intent": "select"}
    memory.trace_hits = []
    memory.schema_hits = []

    memory.per_db_context = {
        "db1": {
            "schema": {"tables": []},
            "generated_sql": "SELECT * FROM users",
            "last_error_message": "syntax error",
        }
    }

    ctx = ContextBuilder.build_for_reflection(memory, "db1")

    assert ctx.user_query == "Show users"
    assert ctx.previous_sql == "SELECT * FROM users"
    assert ctx.error_message == "syntax error"
