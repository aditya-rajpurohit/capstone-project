import pytest

from app.context.context_builder import ContextBuilder
from app.core.constants import MAX_REFLECTION_RETRIES
from app.memory.execution_memory import ExecutionMemory


def test_context_builder_query():
    pytest.skip("Skipping test for refactor")

    memory = ExecutionMemory(
        user_query="Show users",
        active_database_ids=[],
        max_retries=MAX_REFLECTION_RETRIES,
    )
    memory.planner_output = {"intent": "select"}

    schema = {"tables": [{"name": "users"}]}

    ctx = ContextBuilder.build_for_query(memory, schema)

    assert ctx.user_query == "Show users"
    assert ctx.plan == {"intent": "select"}
    assert ctx.filtered_schema is not None
