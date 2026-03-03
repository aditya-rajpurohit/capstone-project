import os

import pytest

from app.agents.critic_agent import CriticAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent
from app.agents.reflection_agent import ReflectionAgent
from app.core.constants import EngineState
from app.inference.models.openai import OpenAI
from app.inference.structured import StructuredModel
from app.orchestration.execution_controller import ExecutionController
from app.tools.db_connector.postgres_connector import PostgresConnector

TEST_DSN = os.getenv("TEST_DSN")
TEST_KEY = os.getenv("OPENAI_API_KEY")

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_workflow():
    if not TEST_DSN:
        pytest.skip("DSN not set!")

    if not TEST_KEY:
        pytest.skip("API_KEY not set!")

    connector = PostgresConnector(str(TEST_DSN))
    await connector.connect()

    # -------------------------
    # Setup DB
    # -------------------------
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

    # -------------------------
    # Setup Agents
    # -------------------------
    backend = OpenAI()
    structured_model = StructuredModel(backend)

    planner = PlannerAgent(structured_model, "gpt-4o-mini")
    query = QueryAgent(structured_model, "gpt-4o-mini")
    reflection = ReflectionAgent()
    critic = CriticAgent(structured_model, "gpt-4o-mini")

    controller = ExecutionController(
        connector=connector,
        planner_agent=planner,
        query_agent=query,
        reflection_agent=reflection,
        critic_agent=critic,
    )

    # -------------------------
    # Controller Execution
    # -------------------------
    trace = await controller.run("Show usernames of all users")

    # -------------------------
    # Assertions
    # -------------------------

    # 1️⃣ Execution result must exist
    assert trace.execution_result is not None
    assert trace.execution_result["status"] in ("success", "failed")

    # 2️⃣ State must be terminal
    assert trace.state in (EngineState.DONE, EngineState.FAILED)

    # 3️⃣ Retry bounded (reflection cap enforced)
    assert trace.retry_count <= 2

    # 4️⃣ Validation metadata must always exist
    assert trace.validation_result is not None
    assert "risk_level" in trace.validation_result
    assert trace.validation_result["risk_level"] in ("low", "medium", "high")

    # 5️⃣ Critic metadata must exist
    assert trace.critic_result is not None
    assert "risk_level" in trace.critic_result
    assert trace.critic_result["risk_level"] in ("low", "medium", "high")

    # 6️⃣ Reflection history consistency
    if trace.retry_count > 0:
        assert len(trace.reflection_history) == trace.retry_count
    else:
        assert trace.reflection_history == []

    # 7️⃣ Scoring must be valid and bounded
    assert trace.final_score is not None
    assert 0.0 <= trace.final_score <= 1.0

    if trace.final_confidence is not None:
        assert 0.0 <= trace.final_confidence <= 1.0
        assert trace.final_score <= trace.final_confidence

    # 8️⃣ Penalties must be non-negative
    assert (trace.risk_penalty or 0) >= 0
    assert (trace.retry_penalty or 0) >= 0
    assert (trace.critic_penalty or 0) >= 0

    # 9️⃣ Execution latency recorded on success
    if trace.execution_result["status"] == "success":
        assert trace.execution_latency_ms is not None
        assert trace.execution_latency_ms >= 0

    # -------------------------
    # Cleanup
    # -------------------------
    await connector.execute("DROP TABLE IF EXISTS users;")
    await connector.close()
