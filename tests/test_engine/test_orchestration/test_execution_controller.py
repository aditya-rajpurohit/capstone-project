import os
import uuid

import pytest
from sqlalchemy import delete
from sqlalchemy.engine import make_url

import app.database.metadata.session as session_module
from app.core.constants import EngineState
from app.database.connectors.postgres_connector import PostgresConnector
from app.database.metadata.models.data_source import DataSourceConfigModel
from app.database.metadata.models.schema_snapshot import SchemaSnapshotModel
from app.database.metadata.snapshot_manager import SnapshotManager
from app.database.registry.database_registry import DatabaseRegistry
from app.engine.agents.critic_agent import CriticAgent
from app.engine.agents.planner_agent import PlannerAgent
from app.engine.agents.query_agent import QueryAgent
from app.engine.agents.reflection_agent import ReflectionAgent
from app.engine.context.chat_context import ChatContext
from app.engine.inference.models.openai import OpenAI
from app.engine.inference.structured_model import StructuredModel
from app.engine.orchestration.execution_controller import ExecutionController
from app.retrieval.embedding_interface import Embedder
from app.retrieval.embedding_models import EmbeddingRecord
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.pgvector_retrieval_backend import PgvectorBackend
from app.retrieval.retrieval_types import RetrievalDocument
from app.runtime.chat.chat_memory import ChatMemory

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TEST_POSTGRES_DSN = os.getenv("TEST_DSN_1")

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class DeterministicEmbedder(Embedder):
    """
    Real retrieval backend, fake deterministic embeddings.
    Good for integration tests because pgvector is exercised,
    but embedding quality does not depend on an external model.
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            seed = sum(ord(ch) for ch in text) % 1000
            base = (seed / 1000.0) or 0.001
            vectors.append([base] * 1536)
        return vectors


def _parse_postgres_dsn(dsn: str) -> dict[str, object]:
    url = make_url(dsn)
    return {
        "host": url.host,
        "port": url.port or 5432,
        "database_name": url.database,
        "username": url.username or "",
        "password": url.password or "",
    }


async def _reset_app_db() -> None:
    Session = session_module.get_async_session()
    async with Session() as session:
        await session.execute(delete(EmbeddingRecord))
        await session.execute(delete(SchemaSnapshotModel))
        await session.execute(delete(DataSourceConfigModel))
        await session.commit()


async def _prepare_target_db(connector: PostgresConnector) -> None:
    await connector.connect()

    await connector.execute("DROP TABLE IF EXISTS users")

    await connector.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL
        )
        """)

    await connector.execute("""
        INSERT INTO users (name)
        VALUES ('Alice'), ('Bob'), ('Charlie')
        """)


async def _cleanup_target_db(connector: PostgresConnector) -> None:
    try:
        await connector.execute("DROP TABLE IF EXISTS users")
    finally:
        await connector.close()


async def _seed_app_db(data_source_id: uuid.UUID, dsn: str) -> None:
    parsed = _parse_postgres_dsn(dsn)

    Session = session_module.get_async_session()
    async with Session() as session:
        session.add(
            DataSourceConfigModel(
                id=data_source_id,
                name="test_postgres",
                dialect="POSTGRES",
                is_active=True,
                host=parsed["host"],
                port=parsed["port"],
                database_name=parsed["database_name"],
                username=parsed["username"],
                encrypted_password=parsed["password"],
                freshness_ttl_seconds=300,
            )
        )

        session.add(
            SchemaSnapshotModel(
                data_source_id=data_source_id,
                version=1,
                snapshot={
                    "version": 1,
                    "tables": [
                        {
                            "name": "users",
                            "columns": [
                                {
                                    "name": "id",
                                    "data_type": "integer",
                                    "is_nullable": False,
                                },
                                {
                                    "name": "name",
                                    "data_type": "text",
                                    "is_nullable": False,
                                },
                            ],
                            "foreign_keys": [],
                        }
                    ],
                },
            )
        )

        await session.commit()


async def _seed_retrieval_index(
    test_id: str,
    data_source_id: uuid.UUID,
) -> HybridRetriever:
    embedder = DeterministicEmbedder()
    backend = PgvectorBackend(embedder=embedder, embedding_dim=1536)

    await backend.upsert(
        [
            RetrievalDocument(
                id=f"schema:test_postgres:users:{test_id}",
                index="schema",
                text="users table with columns id and name",
                metadata={
                    "table": "users",
                    "data_source_id": str(data_source_id),
                },
            ),
            RetrievalDocument(
                id=f"trace:users:list_names:{test_id}",
                index="trace_examples",
                text="Show names of all users -> SELECT id, name FROM users LIMIT 100",
                metadata={
                    "kind": "trace_example",
                    "table": "users",
                },
            ),
        ]
    )

    return HybridRetriever(backend)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execution_workflow():
    if not OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY is not set")

    if not TEST_POSTGRES_DSN:
        pytest.skip("TEST_POSTGRES_DSN is not set")

    test_id = str(uuid.uuid4())
    data_source_id = uuid.uuid4()

    await _reset_app_db()
    DatabaseRegistry._instance = None  # noqa: SLF001
    session_module.engine = None
    session_module._sessionmaker = None

    target_connector = PostgresConnector(TEST_POSTGRES_DSN)
    await _prepare_target_db(target_connector)

    try:
        await _seed_app_db(data_source_id, TEST_POSTGRES_DSN)

        retriever = await _seed_retrieval_index(test_id, data_source_id)

        registry = DatabaseRegistry.get_instance()
        Session = session_module.get_async_session()
        async with Session() as session:
            await registry.load_from_appdb(session)

        llm = StructuredModel(OpenAI())

        planner_agent = PlannerAgent(llm, "gpt-4o-mini")
        query_agent = QueryAgent(llm, "gpt-4o-mini")
        reflection_agent = ReflectionAgent(llm, "gpt-4o-mini")
        critic_agent = CriticAgent(llm, "gpt-4o-mini")

        controller = ExecutionController(
            registry=registry,
            snapshot_manager=SnapshotManager(),
            planner_agent=planner_agent,
            query_agent=query_agent,
            reflection_agent=reflection_agent,
            critic_agent=critic_agent,
            retriever=retriever,
        )

        chat_context = ChatContext(active_database_ids=[str(data_source_id)])
        chat_memory = ChatMemory(session_id=f"integration-real-session-{test_id}")

        trace = await controller.run(
            user_query="Show all users with their id and name",
            chat_context=chat_context,
            chat_memory=chat_memory,
        )

        assert trace.request_id
        assert trace.final_state == EngineState.DONE
        assert trace.plan is not None
        assert trace.per_db_results is not None
        assert str(data_source_id) in trace.per_db_results

        db_result = trace.per_db_results[str(data_source_id)]
        assert db_result["execution_result"]["status"] == "success"
        assert db_result["generated_sql"]
        assert "users" in db_result["generated_sql"].lower()

        assert trace.synthesis_result is not None
        assert trace.synthesis_result["status"] == "success"
        assert trace.synthesis_result["row_count"] >= 3

        rows = trace.synthesis_result["rows"]
        names = {row.get("name") for row in rows if "name" in row}

        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" in names

        trace_second = await controller.run(
            user_query="Show all users with their id and name",
            chat_context=chat_context,
            chat_memory=chat_memory,
        )

        assert trace_second.final_state == EngineState.DONE
        if trace_second.synthesis_result:
            assert trace_second.synthesis_result["status"] == "success"

    finally:
        DatabaseRegistry._instance = None  # noqa: SLF001
        await _reset_app_db()
        await _cleanup_target_db(target_connector)

        session_module.engine = None
        session_module._sessionmaker = None
