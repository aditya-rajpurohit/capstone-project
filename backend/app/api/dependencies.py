
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from app.api.services.session_service import SessionService
from app.api.services.datasource_service import DatasourceService
from app.api.services.query_service import QueryService
from app.api.services.streaming_service import StreamingService
from app.core.security import decode_token
from app.database.metadata.models.user import UserModel
from app.database.registry.database_registry import DatabaseRegistry
from app.database.metadata.session import get_async_session

from app.engine.inference.models import openai
from app.engine.inference.structured_model import StructuredModel
from app.engine.orchestration.execution_controller import ExecutionController
from app.database.registry.database_registry import DatabaseRegistry
from app.database.metadata.snapshot_manager import SnapshotManager

# import your agents + retriever
from app.engine.agents.planner_agent import PlannerAgent
from app.engine.agents.query_agent import QueryAgent
from app.engine.agents.reflection_agent import ReflectionAgent
from app.engine.agents.critic_agent import CriticAgent
from app.retrieval.embedding_interface import Embedder
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.pgvector_retrieval_backend import PgvectorBackend


security = HTTPBearer()

class DummyEmbedder(Embedder):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.001] * 1536 for _ in texts]


def get_database_registry() -> DatabaseRegistry:
    return DatabaseRegistry.get_instance()

def get_session_service() -> SessionService:
    return SessionService()

def get_datasource_service() -> DatasourceService:
    return DatasourceService()

def get_execution_controller() -> ExecutionController:
    registry = DatabaseRegistry.get_instance()
    snapshot_manager = SnapshotManager()

    llm = StructuredModel(openai.OpenAI())
    planner = PlannerAgent(llm, "gpt-4o-mini")
    query = QueryAgent(llm, "gpt-4o-mini")
    reflection = ReflectionAgent(llm, "gpt-4o-mini")
    critic = CriticAgent(llm, "gpt-4o-mini")

    retriever = HybridRetriever(PgvectorBackend(embedder=DummyEmbedder(), embedding_dim=1536))

    return ExecutionController(
        registry=registry,
        snapshot_manager=snapshot_manager,
        planner_agent=planner,
        query_agent=query,
        reflection_agent=reflection,
        critic_agent=critic,
        retriever=retriever,
    )

def get_query_service() -> QueryService:
    return QueryService(get_execution_controller(), get_session_service())

def get_streaming_service(
    query_service: QueryService = Depends(get_query_service),
) -> StreamingService:
    return StreamingService(query_service)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sessionmaker = get_async_session()

    async with sessionmaker() as session:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
