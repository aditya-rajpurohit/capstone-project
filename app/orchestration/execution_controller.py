import datetime

from app.cache.query_cache import QueryCache
from app.context.agent_context import AgentContext
from app.context.chat_context import ChatContext
from app.context.context_builder import ContextBuilder
from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.data_source.snapshot_manager import SnapshotManager
from app.db_registry.database_registry import DatabaseRegistry
from app.memory.chat_memory import ChatMemory
from app.memory.execution_memory import ExecutionMemory
from app.orchestration.policy_engine import PolicyEngine
from app.orchestration.state_machine import StateMachine
from app.retrieval.hybrid_retriever import HybridRetriever
from app.schemas.trace_schema import ExecutionTraceRecord
from app.strategy.db_router import DBRouter
from app.tools.execution_engine import ExecutionEngine
from app.tools.schema_transformer import SchemaTransformer
from app.tools.synthesis_engine import SynthesisEngine


class ExecutionController:

    def __init__(
        self,
        registry: DatabaseRegistry,
        snapshot_manager: SnapshotManager,
        planner_agent,
        query_agent,
        reflection_agent,
        critic_agent,
        retriever: HybridRetriever,
    ):
        self.registry = registry
        self.snapshot_manager = snapshot_manager

        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent
        self.critic_agent = critic_agent

        self.state_machine = StateMachine()
        self.synthesis_engine = SynthesisEngine()
        self.retriever = retriever

        self.query_cache = QueryCache(default_ttl_seconds=300)

    async def run(
        self, user_query: str, chat_context: ChatContext, chat_memory: ChatMemory
    ) -> ExecutionTraceRecord:

        memory = ExecutionMemory(
            user_query=user_query,
            active_database_ids=chat_context.active_database_ids,
            max_retries=MAX_REFLECTION_RETRIES,
        )

        memory.current_state = EngineState.INIT

        # ---------------- Planner (Global) ----------------
        self._transition(memory, EngineState.PLAN)

        planner_context = ContextBuilder.build_for_planner(memory)
        planner_output = await self.planner_agent.run(planner_context)

        # Always retrieve schema hits (scoped to active DBs via metadata filter if you stored data_source_id)
        memory.schema_hits = await self.retriever.retrieve_schema(
            user_query, top_k=8, metadata_filter=None
        )
        # Retrieve past successful traces (examples)
        memory.trace_hits = await self.retriever.retrieve_trace_examples(
            user_query, top_k=3, metadata_filter=None
        )

        memory.planner_output = planner_output.model_dump()
        memory.final_confidence = planner_output.confidence

        routed_database_ids = DBRouter.route(
            user_query, chat_context.active_database_ids, self.registry
        )

        # ---------------- Per-DB Execution ----------------
        for database_id in routed_database_ids:

            database = self.registry.get(database_id)
            if not database:
                continue

            connector = database.connector
            policy = PolicyEngine(dialect=database.dialect)
            execution_engine = ExecutionEngine(connector)
            transformer = SchemaTransformer(database.dialect)

            database_context = {
                "retry_count": 0,
                "reflection_history": [],
            }

            # Use stored snapshot
            snapshot = await self.snapshot_manager.get_snapshot(database_id)
            schema_context = transformer.transform(snapshot)

            database_context["schema"] = schema_context.model_dump()

            # ---------------- QUERY ----------------
            preferred_tables = []
            for hit in memory.schema_hits:
                t = hit.metadata.get("table")
                if t:
                    preferred_tables.append(str(t))

            query_context = ContextBuilder.build_for_query(
                memory,
                database_id,
                database_context[database_id]["schema"],
                preferred_tables,
            )
            query_output = await self.query_agent.run(query_context)

            database_context["generated_sql"] = query_output.sql

            # ---------------- VALIDATION ----------------
            validation = policy.enforce_readonly(query_output.sql)
            database_context["validation"] = validation.model_dump()

            validated_sql = validation.normalized_sql

            if validated_sql is None:
                raise ValueError("ERROR: validated_sql is None.")

            # Build cache key
            snapshot_version = database_context["snapshot_version"]
            cache_key = f"{database_id}::{snapshot_version}::{validated_sql}"

            # Check session memory
            cached = chat_memory.get_query_result(database_id, validated_sql)
            if cached:
                database_context["execution_result"] = cached
                continue

            # Check global cache
            cached = self.query_cache.get(cache_key)
            if cached:
                database_context["execution_result"] = cached
                chat_memory.store_query_result(database_id, validated_sql, cached)
                continue

            # ---------------- EXECUTION ----------------
            execution_result = await execution_engine.execute(validated_sql)
            database_context["execution_result"] = execution_result.model_dump()

            # Cache only if success
            if execution_result.status == "success":
                chat_memory.store_query_result(
                    database_id, validated_sql, database_context["execution_result"]
                )
                self.query_cache.set(
                    cache_key,
                    database_context["execution_result"],
                    database.freshness_ttl_seconds,
                )

            # ---------------- REFLECTION (Per DB) ----------------
            while (
                execution_result.status != "success"
                and database_context["retry_count"] < memory.max_retries
            ):
                database_context["retry_count"] += 1

                reflection_context = ContextBuilder.build_for_reflection(
                    memory, database_id
                )
                reflection_output = await self.reflection_agent.run(reflection_context)

                database_context["generated_sql"] = reflection_output.sql

                validation = policy.enforce_readonly(reflection_output.sql)
                validated_sql = validation.normalized_sql

                if validated_sql is None:
                    raise ValueError("ERROR: validated_sql is None.")

                execution_result = await execution_engine.execute(validated_sql)
                database_context["execution_result"] = execution_result.model_dump()

                if execution_result.status == "success":
                    cache_key = f"{database_id}::{validated_sql}"
                    chat_memory.store_query_result(
                        database_id, validated_sql, database_context["execution_result"]
                    )
                    self.query_cache.set(
                        cache_key,
                        database_context["execution_result"],
                        database.freshness_ttl_seconds,
                    )
                    break

            memory.per_db_context[database_id] = database_context

        # ---------------- Synthesis ----------------
        synthesis = self.synthesis_engine.synthesize(memory.per_db_context)
        memory.synthesis_result = synthesis

        memory.final_state = (
            EngineState.DONE
            if synthesis.get("status") == "success"
            else EngineState.FAILED
        )

        return self._build_trace(memory)

    # ---------------- Helpers ----------------

    def _transition(self, memory, next_state):
        self.state_machine.validate_transition(memory.current_state, next_state)
        memory.current_state = next_state

    def _build_trace(self, memory):

        return ExecutionTraceRecord(
            request_id=memory.request_id,
            user_query=memory.user_query,
            timestamp_iso=datetime.datetime.now(datetime.UTC).isoformat(),
            final_state=memory.final_state,
            retry_count=sum(
                ctx["retry_count"] for ctx in memory.per_db_context.values()
            ),
            plan=memory.planner_output,
            per_db_results=memory.per_db_context,
            synthesis_result=memory.synthesis_result,
            final_confidence=memory.final_confidence,
        )
