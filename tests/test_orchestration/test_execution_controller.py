import os

import pytest

from app.agents.critic import CriticAgent
from app.agents.planner import PlannerAgent
from app.agents.query import QueryAgent
from app.agents.reflection import ReflectionAgent
from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.inference.models.openai import OpenAI
from app.inference.structured import StructuredModel
from app.orchestration.execution_controller import ExecutionController
from app.tools.db_connector.postgres_connector import PostgresConnector

TEST_DSN = os.getenv("TEST_DSN")
TEST_KEY = os.getenv("OPENAI_API_KEY")


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_workflow_refactored():

    if not TEST_DSN:
        pytest.skip("DSN not set!")

    if not TEST_KEY:
        pytest.skip("API_KEY not set!")

    connector = PostgresConnector(str(TEST_DSN))
    await connector.connect()

    # Setup DB
    await connector.execute("DROP TABLE IF EXISTS users;")
    await connector.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            age INT NOT NULL
        );
    """)
    await connector.execute("""
        INSERT INTO users (name, age)
        VALUES
            ('Alice', 25),
            ('Bob', 30),
            ('Charlie', 35);
    """)

    backend = OpenAI()
    structured_model = StructuredModel(backend)

    controller = ExecutionController(
        connector=connector,
        planner_agent=PlannerAgent(structured_model, "gpt-4o-mini"),
        query_agent=QueryAgent(structured_model, "gpt-4o-mini"),
        reflection_agent=ReflectionAgent(structured_model, "gpt-4o-mini"),
        critic_agent=CriticAgent(structured_model, "gpt-4o-mini"),
    )

    trace = await controller.run("Show names of all users")

    # -------- Structural Assertions --------
    assert trace.request_id is not None
    assert trace.user_query == "Show names of all users"
    assert trace.final_state in (EngineState.DONE, EngineState.FAILED)
    assert trace.retry_count <= MAX_REFLECTION_RETRIES

    # -------- Validation + Critic --------
    assert trace.validation_result is not None
    assert trace.critic_result is not None
    assert trace.validation_result["risk_level"] in ("low", "medium", "high")
    assert trace.critic_result["risk_level"] in ("low", "medium", "high")

    # -------- Execution --------
    assert trace.execution_result is not None
    assert trace.execution_result["status"] in ("success", "failed")

    if trace.execution_result["status"] == "success":
        assert trace.execution_latency_ms is not None
        assert trace.execution_latency_ms >= 0

    # -------- Reflection --------
    if trace.retry_count > 0:
        assert len(trace.reflection_history) == trace.retry_count
    else:
        assert trace.reflection_history == []

    # -------- Scoring --------
    assert trace.final_score is not None
    assert 0.0 <= trace.final_score <= 1.0

    if trace.final_confidence is not None:
        assert 0.0 <= trace.final_confidence <= 1.0
        assert trace.final_score <= trace.final_confidence

    # Cleanup
    await connector.execute("DROP TABLE IF EXISTS users;")
    await connector.close()
