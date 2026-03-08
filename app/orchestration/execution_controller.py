import datetime

from app.context.context_builder import ContextBuilder
from app.memory.execution_memory import ExecutionMemory
from app.orchestration.state_machine import StateMachine
from app.orchestration.policy_engine import PolicyEngine
from app.registry.database_registry import DatabaseRegistry
from app.schemas.trace_schema import ExecutionTraceRecord
from app.tools.execution_engine import ExecutionEngine
from app.tools.schema_transformer import SchemaTransformer
from app.tools.synthesis_engine import SynthesisEngine
from app.core.constants import EngineState, MAX_REFLECTION_RETRIES


class ExecutionController:

    def __init__(
        self,
        registry: DatabaseRegistry,
        planner_agent,
        query_agent,
        reflection_agent,
        critic_agent,
    ):
        self.registry = registry
        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent
        self.critic_agent = critic_agent

        self.state_machine = StateMachine()
        self.synthesis_engine = SynthesisEngine()

    async def run(self, user_query: str, chat_context) -> ExecutionTraceRecord:

        memory = ExecutionMemory(
            user_query=user_query,
            active_db_ids=chat_context.active_db_ids,
            max_retries=MAX_REFLECTION_RETRIES,
        )

        memory.current_state = EngineState.INIT

        # ---------------- Planner (Global) ----------------
        self._transition(memory, EngineState.PLAN)

        planner_context = ContextBuilder.build_for_planner(memory)
        planner_output = await self.planner_agent.run(planner_context)
        memory.planner_output = planner_output.model_dump()
        memory.final_confidence = planner_output.confidence

        # ---------------- Per-DB Execution ----------------
        for db_id in memory.active_db_ids:

            db_unit = self.registry.get(db_id)
            if not db_unit:
                continue

            connector = db_unit.connector
            policy = PolicyEngine(dialect=connector.dialect)
            execution_engine = ExecutionEngine(connector)
            transformer = SchemaTransformer(connector.dialect)

            db_ctx = {
                "retry_count": 0,
                "reflection_history": [],
            }

            # SCHEMA
            raw_schema = await connector.introspect_schema()
            schema_context = transformer.transform(raw_schema)
            db_ctx["schema"] = schema_context.model_dump()

            # QUERY
            query_context = ContextBuilder.build_for_query(memory)
            query_output = await self.query_agent.run(query_context)

            db_ctx["generated_sql"] = query_output.sql

            # VALIDATION
            validation = policy.enforce_readonly(query_output.sql)
            db_ctx["validation"] = validation.model_dump()
            validated_sql = validation.normalized_sql

            # EXECUTION
            if validated_sql is None:
                raise ValueError("ERROR: validated_sql is None!")
            execution_result = await execution_engine.execute(validated_sql)
            db_ctx["execution_result"] = execution_result.model_dump()

            # Reflection per DB
            while (
                execution_result.status != "success"
                and db_ctx["retry_count"] < memory.max_retries
            ):
                db_ctx["retry_count"] += 1

                reflection_context = ContextBuilder.build_for_reflection(memory)
                reflection_output = await self.reflection_agent.run(
                    reflection_context
                )

                db_ctx["generated_sql"] = reflection_output.sql

                validation = policy.enforce_readonly(reflection_output.sql)
                validated_sql = validation.normalized_sql

                if validated_sql is None:
                    raise ValueError("ERROR: validated_sql is None!")
                
                execution_result = await execution_engine.execute(validated_sql)
                db_ctx["execution_result"] = execution_result.model_dump()

            memory.per_db_context[db_id] = db_ctx

        # ---------------- Synthesis ----------------
        synthesis = self.synthesis_engine.synthesize(memory.per_db_context)
        memory.synthesis_result = synthesis

        memory.final_state = (
            EngineState.DONE
            if synthesis.get("status") == "success"
            else EngineState.FAILED
        )

        return self._build_trace(memory)

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
