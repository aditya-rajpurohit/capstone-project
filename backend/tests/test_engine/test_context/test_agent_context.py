from app.engine.context.agent_context import AgentContext


def test_agent_context():
    ctx = AgentContext(
        user_query="test query",
        plan={"intent": "select"},
        filtered_schema={"tables": []},
        previous_sql="SELECT 1",
        error_message="error",
    )

    assert ctx.user_query == "test query"
    assert ctx.plan == {"intent": "select"}
    assert ctx.filtered_schema == {"tables": []}
    assert ctx.previous_sql == "SELECT 1"
    assert ctx.error_message == "error"


def test_agent_context_default_lists():
    ctx = AgentContext(user_query="test")

    assert ctx.trace_hits == []
    assert ctx.schema_hits == []
