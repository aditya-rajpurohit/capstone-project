import os
import uuid

import pytest
from sqlalchemy import delete

from app.engine.agents.critic_agent import CriticAgent
from app.engine.agents.planner_agent import PlannerAgent
from app.engine.agents.query_agent import QueryAgent
from app.engine.agents.reflection_agent import ReflectionAgent
from app.engine.context.chat_context import ChatContext
from app.core.constants import DatabaseDialect, EngineState
from app.database.metadata.models.data_source import DataSourceConfigModel
from app.database.metadata.models.schema_snapshot import SchemaSnapshotModel
from app.database.metadata.session import get_async_session
from app.database.metadata.snapshot_manager import SnapshotManager
from app.database.registry.database_registry import DatabaseRegistry, DataSourceHandle
from app.engine.inference.models.openai import OpenAI
from app.engine.inference.structured_model import StructuredModel
from app.engine.orchestration.execution_controller import ExecutionController
from app.database.connector.postgres_connector import PostgresConnector

pytestmark = pytest.mark.integration

TEST_DSN_DB1 = os.getenv("TEST_DSN_1")
TEST_DSN_DB2 = os.getenv("TEST_DSN_2")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def _normalized_users_snapshot(
    dialect: DatabaseDialect = DatabaseDialect.POSTGRES,
) -> dict:
    return {
        "dialect": dialect,
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "data_type": "integer", "is_nullable": False},
                    {"name": "name", "data_type": "text", "is_nullable": False},
                    {"name": "age", "data_type": "integer", "is_nullable": False},
                ],
                "foreign_keys": [],
            }
        ],
    }


@pytest.mark.asyncio
async def test_execution_orchestration():

    pytest.skip("Skipping test for refactor")

    # if not (TEST_DSN_DB1 and TEST_DSN_DB2 and DATABASE_URL and OPENAI_API_KEY):
    #     pytest.skip(
    #         "Missing required env vars: TEST_DSN_DB1/DB2, DATABASE_URL, OPENAI_API_KEY"
    #     )

    Session = get_async_session()

    async with Session() as session:
        await session.execute(delete(SchemaSnapshotModel))
        await session.execute(delete(DataSourceConfigModel))
        await session.commit()

    # -------------------------
    # Setup two real DBs
    # -------------------------
    c1 = PostgresConnector(TEST_DSN_DB1)
    c2 = PostgresConnector(TEST_DSN_DB2)

    await c1.connect()
    await c2.connect()

    for c in (c1, c2):
        await c.execute("DROP TABLE IF EXISTS users;")
        await c.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                age INT NOT NULL
            );
        """)

    await c1.execute("""
        INSERT INTO users (name, age)
        VALUES ('Alice', 25), ('Bob', 30);
    """)
    await c2.execute("""
        INSERT INTO users (name, age)
        VALUES ('Charlie', 35), ('Dora', 28);
    """)

    # -------------------------
    # Seed App DB: data_sources + schema_snapshots
    # -------------------------
    ds1_id = uuid.uuid4()
    ds2_id = uuid.uuid4()

    Session = get_async_session()

    async with Session() as session:
        session.add_all(
            [
                DataSourceConfigModel(
                    id=ds1_id,
                    name="db1",
                    dialect=DatabaseDialect.POSTGRES,
                    is_active=True,
                    host="localhost",
                    port=5432,
                    database_name="test_agentic_db_1",
                    username="adityarajpurohit",
                    encrypted_password="postgres",
                ),
                DataSourceConfigModel(
                    id=ds2_id,
                    name="db2",
                    dialect=DatabaseDialect.POSTGRES,
                    is_active=True,
                    host="localhost",
                    port=5432,
                    database_name="test_agentic_db_2",
                    username="adityarajpurohit",
                    encrypted_password="postgres",
                ),
            ]
        )
        await session.commit()

        session.add_all(
            [
                SchemaSnapshotModel(
                    data_source_id=ds1_id,
                    version=1,
                    snapshot=_normalized_users_snapshot(),
                ),
                SchemaSnapshotModel(
                    data_source_id=ds2_id,
                    version=1,
                    snapshot=_normalized_users_snapshot(),
                ),
            ]
        )
        await session.commit()

        # Register runtime handles in registry
        registry = DatabaseRegistry.get_instance()
        await registry.load_from_appdb(session)

    # -------------------------
    # Setup controller + agents
    # -------------------------
    backend = OpenAI()
    structured_model = StructuredModel(backend)

    controller = ExecutionController(
        registry=registry,
        snapshot_manager=SnapshotManager(),
        planner_agent=PlannerAgent(structured_model, "gpt-4o-mini"),
        query_agent=QueryAgent(structured_model, "gpt-4o-mini"),
        reflection_agent=ReflectionAgent(structured_model, "gpt-4o-mini"),
        critic_agent=CriticAgent(structured_model, "gpt-4o-mini"),
    )

    chat_context = ChatContext(active_database_ids=[str(ds1_id), str(ds2_id)])

    trace = await controller.run("Show names of all users", chat_context=chat_context)
    print(trace)
    # -------------------------
    # Assertions
    # -------------------------
    assert trace.final_state in (EngineState.DONE, EngineState.FAILED)

    # We expect success in this happy path
    assert trace.final_state == EngineState.DONE
    assert trace.synthesis_result is not None
    assert trace.synthesis_result["status"] == "success"

    # Both DBs should have executed successfully
    assert set(trace.synthesis_result["successful_db_ids"]) == {
        str(ds1_id),
        str(ds2_id),
    }
    assert trace.synthesis_result["failed_db_ids"] == []

    # Union merge should contain 4 rows total
    assert trace.synthesis_result["row_count"] == 4
    assert len(trace.synthesis_result["rows"]) == 4

    # per-db results present
    assert trace.per_db_results is not None
    assert str(ds1_id) in trace.per_db_results
    assert str(ds2_id) in trace.per_db_results
    assert trace.per_db_results[str(ds1_id)]["execution_result"]["status"] == "success"
    assert trace.per_db_results[str(ds2_id)]["execution_result"]["status"] == "success"

    # -------------------------
    # Cleanup DBs
    # -------------------------
    for c in (c1, c2):
        await c.execute("DROP TABLE IF EXISTS users;")
        await c.close()
