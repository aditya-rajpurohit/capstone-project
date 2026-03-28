from unittest.mock import AsyncMock

import pytest

from app.engine.agents.planner_agent import PlannerAgent
from app.engine.context.agent_context import AgentContext
from app.engine.contracts.planner_contract import PlannerOutput


@pytest.mark.asyncio
async def test_planner_agent():
    mock_model = AsyncMock()
    mock_model.generate.return_value = PlannerOutput(
        intent="Test",
        entities=[],
        constraints=[],
        confidence=0.9,
    )

    agent = PlannerAgent(mock_model, "mock-model")
    ctx = AgentContext(user_query="test")

    # assert result.intent == "Test"
