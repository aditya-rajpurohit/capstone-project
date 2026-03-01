import pytest
from app.tools.db_connector.postgres_connector import PostgresConnector
from app.orchestration.execution_controller import ExecutionController

TEST_DSN = "postgresql://adityarajpurohit:postgres@localhost:5432/test_agentic_db"

@pytest.mark.asyncio
async def test_full_workflow():
    connector = PostgresConnector(TEST_DSN)
    await connector.connect()

    # test schema
    await connector.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            age INT
        );
    """)

    await connector.execute("""
        INSERT INTO users (name, age)
        VALUES ('Alice', 25), ('Bob', 30)
        ON CONFLICT DO NOTHING;
    """)

    controller = ExecutionController(connector)
    trace = await controller.run("Show all users")

    assert trace.state.name in ["DONE", "FAILED"]

    if trace.execution_result is not None:
        assert trace.execution_result["status"] == "success"

    await connector.execute("DROP TABLE IF EXISTS users;")

    await connector.close()
