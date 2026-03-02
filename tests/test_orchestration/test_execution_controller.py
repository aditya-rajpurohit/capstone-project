import pytest
import os
from app.inference.models.anthropic import Anthropic
from app.inference.structured import StructuredModel
from app.tools.db_connector.postgres_connector import PostgresConnector
from app.orchestration.execution_controller import ExecutionController
from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent

TEST_DSN = os.getenv("TEST_DSN")
TEST_KEY = os.getenv("ANTHROPIC_API_KEY")

@pytest.mark.asyncio
async def test_full_workflow():
    if not TEST_DSN:
        pytest.skip("DSN not set!")
    
    if not TEST_KEY:
        pytest.skip("API_KEY not set!")

    connector = PostgresConnector(str(TEST_DSN))
    await connector.connect()


    # ----------------------
    # 1️⃣ Setup Test Schema
    # ----------------------
    await connector.execute("""
        DROP TABLE IF EXISTS users;
    """)

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


    # ----------------------
    # 2️⃣ Setup Agents
    # ----------------------

    backend = Anthropic()
    structured_model = StructuredModel(backend)

    planner = PlannerAgent(structured_model, "claude-3-haiku-20240307")
    query = QueryAgent(structured_model, "claude-3-haiku-20240307")

    controller = ExecutionController(connector=connector, planner_agent=planner, query_agent=query)

    # ----------------------
    # 3️⃣ Run NL Query
    # ----------------------

    trace = await controller.run("List all user names ordered by id")

    print("Generated Query:", trace.generated_query)
    print("Execution Result:", trace.execution_result)

    assert trace.execution_result is not None
    assert trace.execution_result["status"] == "success"

    rows = trace.execution_result["rows"]
    
    
    # ----------------------
    # 4️⃣ Validate Output
    # ----------------------

    expected = [
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"},
    ]

    result_names = [{"name": row["name"]} for row in rows]

    assert result_names == expected


    # ----------------------
    # 5️⃣ Cleanup
    # ----------------------

    await connector.execute("DROP TABLE IF EXISTS users;")

    await connector.close()
