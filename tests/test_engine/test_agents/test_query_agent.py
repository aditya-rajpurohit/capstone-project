from unittest.mock import AsyncMock

import pytest

from app.engine.agents.query_agent import QueryAgent
from app.engine.context.agent_context import AgentContext
from app.engine.contracts.query_contract import QueryOutput


@pytest.mark.asyncio
async def test_query_agent():
    mock_model = AsyncMock()
    mock_model.generate.return_value = QueryOutput(
        sql="SELECT 1",
        confidence=0.8,
    )

    agent = QueryAgent(mock_model, "mock")
    ctx = AgentContext(
        user_query="test", plan={"intent": "x"}, filtered_schema={"tables": []}
    )

    result = await agent.run(ctx)
    # assert result.sql == "SELECT 1"
