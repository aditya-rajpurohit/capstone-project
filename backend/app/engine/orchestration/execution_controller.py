# class ExecutionController:

#     def __init__(
#         self,
#         registry: DatabaseRegistry,
#         snapshot_manager: SnapshotManager,
#         planner_agent,
#         query_agent,
#         reflection_agent,
#         critic_agent,
#         retriever: HybridRetriever,
#     ):
#         self.registry = registry
#         self.snapshot_manager = snapshot_manager

#         self.planner_agent = planner_agent
#         self.query_agent = query_agent
#         self.reflection_agent = reflection_agent
#         self.critic_agent = critic_agent

#         self.retriever = retriever
#         self.state_machine = StateMachine()
#         self.synthesis_engine = SynthesisEngine()

#         self.query_cache = QueryCache(default_ttl_seconds=300)
#         self.rate_limit = RateLimiter()

#     # ==============================================================
#     # Planner Phase
#     # ==============================================================

#     async def _plan_phase(self, memory: ExecutionMemory):

#         self._transition(memory, EngineState.PLAN)

#         context = ContextBuilder.build_for_planner(memory)
#         planner_output = await self.planner_agent.run(context)

#         memory.planner_output = planner_output.model_dump()
#         memory.final_confidence = planner_output.confidence

#     # ==============================================================
#     # Retrieval Phase
#     # ==============================================================

#     async def _retrieve_phase(self, memory: ExecutionMemory):
#         memory.schema_hits = await self.retriever.retrieve_schema_hits(
#             memory.user_query, top_k=8
#         )
#         memory.trace_hits = await self.retriever.retrieve_trace_hits(
#             memory.user_query, top_k=3
#         )

#     # ==============================================================
#     # Per-DB Execution
#     # ==============================================================

#     async def _execute_for_db(
#         self,
#         memory: ExecutionMemory,
#         db_id: str,
#         chat_memory: ChatMemory,
#     ):

#         handle = self.registry.get(db_id)
#         if not handle or not handle.is_active:
#             return

#         connector = handle.connector
#         policy = SqlPolicyEngine(dialect=handle.dialect)
#         execution_engine = ExecutionEngine(connector)
#         transformer = SchemaTransformer(handle.dialect)

#         memory.init_db_context(db_id)
#         db_ctx = memory.per_db_context[db_id]

#         # Snapshot
#         snapshot = await self.snapshot_manager.get_snapshot(db_id)
#         schema_context = transformer.transform(snapshot)

#         db_ctx["schema"] = schema_context.model_dump()
#         db_ctx["snapshot_version"] = snapshot.get("version", 1)

#         # Query generation
#         query_context = ContextBuilder.build_for_query(memory, db_id, db_ctx["schema"])

#         query_output = await self.query_agent.run(query_context)
#         db_ctx["generated_sql"] = query_output.sql

#         # Validation
#         validation = policy.enforce_readonly(query_output.sql)
#         validated_sql = validation.normalized_sql

#         if validated_sql is None:
#             raise RuntimeError("validated_sql is None")

#         # Execute (with cache)
#         execution_result = await self._handle_execution_with_cache(
#             db_id,
#             validated_sql,
#             db_ctx["snapshot_version"],
#             execution_engine,
#             chat_memory,
#             handle.freshness_ttl_seconds,
#         )

#         db_ctx["execution_result"] = execution_result

#         # Reflection loop
#         if execution_result.get("status") != "success":
#             await self._reflection_loop(
#                 memory,
#                 db_id,
#                 execution_engine,
#                 policy,
#                 chat_memory,
#                 handle.freshness_ttl_seconds,
#             )

#     # ==============================================================
#     # Execution + Cache Handling
#     # ==============================================================

#     async def _handle_execution_with_cache(
#         self,
#         db_id: str,
#         validated_sql: str,
#         snapshot_version: int,
#         execution_engine: ExecutionEngine,
#         chat_memory: ChatMemory,
#         ttl: int,
#     ) -> dict[str, Any]:

#         cache_key = f"{db_id}::{snapshot_version}::{validated_sql}"

#         # Session cache
#         cached = chat_memory.get_query_result(db_id, validated_sql)
#         if cached:
#             return cached

#         # Global cache
#         cached = self.query_cache.get(cache_key)
#         if cached:
#             chat_memory.store_query_result(db_id, validated_sql, cached)
#             return cached

#         # Execute
#         result = await execution_engine.execute(validated_sql)
#         result_dict = result.model_dump()

#         if result.status == "success":
#             chat_memory.store_query_result(db_id, validated_sql, result_dict)
#             self.query_cache.set(cache_key, result_dict, ttl)

#         return result_dict

#     # ==============================================================
#     # Reflection Loop
#     # ==============================================================

#     async def _reflection_loop(
#         self,
#         memory: ExecutionMemory,
#         db_id: str,
#         execution_engine: ExecutionEngine,
#         policy: SqlPolicyEngine,
#         chat_memory: ChatMemory,
#         ttl: int,
#     ):

#         db_ctx = memory.per_db_context[db_id]

#         while (
#             db_ctx["execution_result"]["status"] != "success"
#             and db_ctx["retry_count"] < memory.max_retries
#         ):
#             db_ctx["retry_count"] += 1

#             reflection_context = ContextBuilder.build_for_reflection(memory, db_id)
#             reflection_output = await self.reflection_agent.run(reflection_context)
#             db_ctx["generated_sql"] = reflection_output.sql

#             validation = policy.enforce_readonly(reflection_output.sql)
#             validated_sql = validation.normalized_sql

#             if validated_sql is None:
#                 break

#             result = await execution_engine.execute(validated_sql)
#             result_dict = result.model_dump()

#             db_ctx["execution_result"] = result_dict

#             if result.status == "success":
#                 cache_key = f"{db_id}::{validated_sql}"
#                 chat_memory.store_query_result(db_id, validated_sql, result_dict)
#                 self.query_cache.set(cache_key, result_dict, ttl)
#                 break

#     # ==============================================================
#     # Finalization
#     # ==============================================================

#     def _finalize(self, memory: ExecutionMemory):

#         synthesis = self.synthesis_engine.synthesize(memory.per_db_context)
#         memory.synthesis_result = synthesis

#         memory.final_state = (
#             EngineState.DONE
#             if synthesis.get("status") == "success"
#             else EngineState.FAILED
#         )

#     # ==============================================================
#     # Helpers
#     # ==============================================================

#     def _transition(self, memory: ExecutionMemory, next_state: EngineState):
#         self.state_machine.validate_transition(
#             EngineState(memory.current_state), next_state
#         )
#         memory.current_state = next_state

#     def _build_trace(self, memory: ExecutionMemory) -> ExecutionTraceRecord:

#         return ExecutionTraceRecord(
#             request_id=memory.request_id,
#             user_query=memory.user_query,
#             timestamp_iso=datetime.datetime.now(datetime.UTC).isoformat(),
#             final_state=EngineState(memory.final_state),
#             retry_count=memory.total_retry_count(),
#             plan=memory.planner_output,
#             per_db_results=memory.per_db_context,
#             synthesis_result=memory.synthesis_result,
#             final_confidence=memory.final_confidence,
#         )

#     # ==============================================================
#     # Public Entry
#     # ==============================================================

#     async def run(
#         self,
#         user_query: str,
#         chat_context: ChatContext,
#         chat_memory: ChatMemory,
#     ) -> ExecutionTraceRecord:

#         trace = TraceContext()
#         latentcy = LatencyTracker()

#         if PromptInjectionDetector.detect(user_query):
#             raise RuntimeError("ERROR: Prompt Injection")

#         if not self.rate_limit.allow(chat_memory.session_id):
#             raise RuntimeError("ERROR: Rate Limit Exceeded")

#         memory = ExecutionMemory(
#             user_query=user_query,
#             active_database_ids=chat_context.active_database_ids,
#             max_retries=MAX_REFLECTION_RETRIES,
#         )

#         memory.current_state = EngineState.INIT

#         await self._plan_phase(memory)
#         await self._retrieve_phase(memory)

#         routed_ids = DBRouter.route(
#             user_query,
#             chat_context.active_database_ids,
#             self.registry,
#         )

#         for db_id in routed_ids:
#             await self._execute_for_db(memory, db_id, chat_memory)

#         self._finalize(memory)

#         return self._build_trace(memory)


import datetime
from typing import Any

from app.cache.query_cache import QueryCache
from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.database.execution.execution_engine import ExecutionEngine
from app.database.execution.synthesis_engine import SynthesisEngine
from app.database.metadata.schema_transformer import SchemaTransformer
from app.database.metadata.snapshot_manager import SnapshotManager
from app.database.registry.database_registry import DatabaseRegistry
from app.engine.context.chat_context import ChatContext
from app.engine.context.context_builder import ContextBuilder
from app.engine.contracts.trace_schema import ExecutionTraceRecord
from app.engine.orchestration.state_machine import StateMachine
from app.engine.strategy.db_router import DBRouter
from app.evals.guardrails.policy_engine import SqlPolicyEngine
from app.evals.guardrails.prompt_injection_detector import \
    PromptInjectionDetector
from app.evals.guardrails.query_cost_estimator import QueryCostEstimator
from app.evals.guardrails.rate_limiter import RateLimiter
from app.evals.observability.logger import logger
from app.evals.observability.metrics import LatencyTracker
from app.evals.observability.tracer import TraceContext
from app.retrieval.hybrid_retriever import HybridRetriever
from app.runtime.chat.chat_memory import ChatMemory
from app.runtime.execution.execution_memory import ExecutionMemory


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
    ) -> None:
        self.registry = registry
        self.snapshot_manager = snapshot_manager

        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent
        self.critic_agent = critic_agent

        self.retriever = retriever
        self.state_machine = StateMachine()
        self.synthesis_engine = SynthesisEngine()

        self.query_cache = QueryCache(default_ttl_seconds=300)
        self.rate_limiter = RateLimiter()

    # ==============================================================
    # Public Entry
    # ==============================================================

    async def run(
        self,
        user_query: str,
        chat_context: ChatContext,
        chat_memory: ChatMemory,
    ) -> ExecutionTraceRecord:
        trace = TraceContext()
        latency = LatencyTracker()

        logger.info(f"[{trace.trace_id}] Start query: {user_query}")

        memory = self._init_memory(user_query, chat_context)

        self._guardrails(memory, chat_memory)

        await self._plan(memory)

        await self._retrieve(memory)

        routed_ids = self._route(memory, chat_context)

        await self._execute_all(memory, routed_ids, chat_memory)

        self._finalize(memory)

        logger.info(
            f"[{trace.trace_id}] Finished in {latency.elapsed_ms()} ms | state={memory.final_state}"
        )

        return self._build_trace(memory)

    # ==============================================================
    # Layered Pipeline Steps
    # ==============================================================

    def _init_memory(
        self,
        user_query: str,
        chat_context: ChatContext,
    ) -> ExecutionMemory:
        memory = ExecutionMemory(
            user_query=user_query,
            active_database_ids=chat_context.active_database_ids,
            max_retries=MAX_REFLECTION_RETRIES,
        )
        memory.current_state = EngineState.INIT
        return memory

    def _guardrails(
        self,
        memory: ExecutionMemory,
        chat_memory: ChatMemory,
    ) -> None:
        if PromptInjectionDetector.detect(memory.user_query):
            raise RuntimeError("Prompt injection detected")

        if not self.rate_limiter.allow(chat_memory.session_id):
            raise RuntimeError("Rate limit exceeded")

    async def _plan(self, memory: ExecutionMemory) -> None:
        self._transition(memory, EngineState.PLAN)

        context = ContextBuilder.build_for_planner(memory)
        planner_output = await self.planner_agent.run(context)

        memory.planner_output = planner_output.model_dump()
        memory.final_confidence = planner_output.confidence

    async def _retrieve(self, memory: ExecutionMemory) -> None:
        memory.schema_hits = await self.retriever.retrieve_schema_hits(
            memory.user_query,
            top_k=8,
        )
        memory.trace_hits = await self.retriever.retrieve_trace_hits(
            memory.user_query,
            top_k=3,
        )

    def _route(
        self,
        memory: ExecutionMemory,
        chat_context: ChatContext,
    ) -> list[str]:
        return DBRouter.route(
            memory.user_query,
            chat_context.active_database_ids,
            self.registry,
        )

    async def _execute_all(
        self,
        memory: ExecutionMemory,
        routed_ids: list[str],
        chat_memory: ChatMemory,
    ) -> None:
        for db_id in routed_ids:
            await self._execute_single_db(memory, db_id, chat_memory)

    async def _execute_single_db(
        self,
        memory: ExecutionMemory,
        db_id: str,
        chat_memory: ChatMemory,
    ) -> None:
        handle = self.registry.get(db_id)
        if not handle or not handle.is_active:
            return

        memory.init_db_context(db_id)
        db_ctx = memory.per_db_context[db_id]

        connector = handle.connector
        execution_engine = ExecutionEngine(connector)
        policy = SqlPolicyEngine(dialect=handle.dialect)
        transformer = SchemaTransformer(handle.dialect)

        # -------------------------
        # Load schema
        # -------------------------
        snapshot = await self.snapshot_manager.get_snapshot(db_id)
        schema_context = transformer.transform(snapshot)

        db_ctx["schema"] = schema_context.model_dump()
        db_ctx["snapshot_version"] = snapshot.get("version", 1)

        # -------------------------
        # Query generation
        # -------------------------
        self._transition(memory, EngineState.QUERY_GENERATION)

        context = ContextBuilder.build_for_query(
            memory,
            db_id,
            db_ctx["schema"],
        )
        query_output = await self.query_agent.run(context)

        db_ctx["generated_sql"] = query_output.sql

        # -------------------------
        # Validation
        # -------------------------
        self._transition(memory, EngineState.VALIDATION)

        validation = policy.enforce_readonly(query_output.sql)
        validated_sql = validation.normalized_sql
        db_ctx["validation"] = validation.model_dump()

        if validated_sql is None:
            raise RuntimeError("validated_sql is None")

        # -------------------------
        # Cost check
        # -------------------------
        cost = QueryCostEstimator.estimate(validated_sql)
        db_ctx["query_cost"] = cost

        if cost == "high":
            raise RuntimeError("Query too expensive")

        # -------------------------
        # Execution
        # -------------------------
        self._transition(memory, EngineState.EXECUTION)

        result = await self._handle_execution_with_cache(
            db_id=db_id,
            validated_sql=validated_sql,
            snapshot_version=db_ctx["snapshot_version"],
            execution_engine=execution_engine,
            chat_memory=chat_memory,
            ttl=handle.freshness_ttl_seconds,
        )

        db_ctx["execution_result"] = result

        # -------------------------
        # Reflection
        # -------------------------
        if result.get("status") != "success":
            await self._reflection(
                memory=memory,
                db_id=db_id,
                execution_engine=execution_engine,
                policy=policy,
                chat_memory=chat_memory,
                handle=handle,
            )

    async def _handle_execution_with_cache(
        self,
        db_id: str,
        validated_sql: str,
        snapshot_version: int,
        execution_engine: ExecutionEngine,
        chat_memory: ChatMemory,
        ttl: int,
    ) -> dict[str, Any]:
        cache_key = f"{db_id}::{snapshot_version}::{validated_sql}"

        cached = chat_memory.get_query_result(db_id, validated_sql)
        if cached:
            return cached

        cached = self.query_cache.get(cache_key)
        if cached:
            chat_memory.store_query_result(db_id, validated_sql, cached)
            return cached

        result = await execution_engine.execute(validated_sql)
        result_dict = result.model_dump()

        if result.status == "success":
            chat_memory.store_query_result(db_id, validated_sql, result_dict)
            self.query_cache.set(cache_key, result_dict, ttl)

        return result_dict

    async def _reflection(
        self,
        memory: ExecutionMemory,
        db_id: str,
        execution_engine: ExecutionEngine,
        policy: SqlPolicyEngine,
        chat_memory: ChatMemory,
        handle,
    ) -> None:
        db_ctx = memory.per_db_context[db_id]

        while (
            db_ctx["execution_result"]["status"] != "success"
            and db_ctx["retry_count"] < memory.max_retries
        ):
            db_ctx["retry_count"] += 1

            self._transition(memory, EngineState.REFLECTION)

            context = ContextBuilder.build_for_reflection(memory, db_id)
            output = await self.reflection_agent.run(context)

            db_ctx["generated_sql"] = output.sql

            self._transition(memory, EngineState.QUERY_GENERATION)

            validation = policy.enforce_readonly(output.sql)
            db_ctx["validation"] = validation.model_dump()

            validated_sql = validation.normalized_sql
            if validated_sql is None:
                break

            cost = QueryCostEstimator.estimate(validated_sql)
            db_ctx["query_cost"] = cost
            if cost == "high":
                break

            self._transition(memory, EngineState.VALIDATION)
            self._transition(memory, EngineState.EXECUTION)

            result = await execution_engine.execute(validated_sql)
            result_dict = result.model_dump()

            db_ctx["execution_result"] = result_dict

            if result.status == "success":
                snapshot_version = db_ctx.get("snapshot_version", 1)
                cache_key = f"{db_id}::{snapshot_version}::{validated_sql}"
                chat_memory.store_query_result(db_id, validated_sql, result_dict)
                self.query_cache.set(
                    cache_key, result_dict, handle.freshness_ttl_seconds
                )
                break

    def _finalize(self, memory: ExecutionMemory) -> None:
        synthesis = self.synthesis_engine.synthesize(memory.per_db_context)
        memory.synthesis_result = synthesis

        if synthesis.get("status") == "success":
            self._transition(memory, EngineState.DONE)
        else:
            self._transition(memory, EngineState.FAILED)

        memory.final_state = memory.current_state

    # ==============================================================
    # Helpers
    # ==============================================================

    def _transition(
        self,
        memory: ExecutionMemory,
        next_state: EngineState,
    ) -> None:
        self.state_machine.validate_transition(
            EngineState(memory.current_state), next_state
        )
        memory.current_state = next_state

    def _build_trace(self, memory: ExecutionMemory) -> ExecutionTraceRecord:
        return ExecutionTraceRecord(
            request_id=memory.request_id,
            user_query=memory.user_query,
            timestamp_iso=datetime.datetime.now(datetime.UTC).isoformat(),
            final_state=EngineState(memory.final_state),
            retry_count=memory.total_retry_count(),
            plan=memory.planner_output,
            per_db_results=memory.per_db_context,
            synthesis_result=memory.synthesis_result,
            final_confidence=memory.final_confidence,
        )
