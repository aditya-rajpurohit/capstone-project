import datetime

from app.agents.base import BaseAgent
from app.context.context_builder import ContextBuilder
from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.core.exceptions import PolicyViolationError
from app.memory.execution_memory import ExecutionMemory
from app.orchestration.policy_engine import PolicyEngine
from app.orchestration.state_machine import StateMachine
from app.schemas.execution_schema import ExecutionResult
from app.schemas.trace_schema import ExecutionTraceRecord
from app.tools.db_connector.base_connector import BaseConnector
from app.tools.execution_engine import ExecutionEngine
from app.tools.schema_transformer import SchemaTransformer


def _compute_score(
    model_confidence: float,
    validation_result: dict | None,
    critic_result: dict | None,
    retry_count: int,
) -> tuple[float, float, float, float]:

    risk_penalty = 0.0
    if validation_result:
        if validation_result.get("risk_level") == "medium":
            risk_penalty = 0.1
        elif validation_result.get("risk_level") == "high":
            risk_penalty = 0.2

    critic_penalty = 0.0
    if critic_result:
        if critic_result.get("risk_level") == "medium":
            critic_penalty = 0.1
        elif critic_result.get("risk_level") == "high":
            critic_penalty = 0.2

    retry_penalty = retry_count * 0.05

    final_score = max(
        0.0,
        model_confidence - risk_penalty - critic_penalty - retry_penalty,
    )

    return final_score, risk_penalty, critic_penalty, retry_penalty


class ExecutionController:
    """
    Deterministic Orchestrator.
    Owns execution flow.
    Owns ExecutionMemory.
    StateMachine only validates transitions.
    """

    def __init__(
        self,
        connector: BaseConnector,
        planner_agent: BaseAgent,
        query_agent: BaseAgent,
        reflection_agent: BaseAgent,
        critic_agent: BaseAgent,
    ) -> None:

        self.connector = connector
        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent
        self.critic_agent = critic_agent

        self.state_machine = StateMachine()

        self.policy_engine = PolicyEngine(dialect=connector.dialect)
        self.execution_engine = ExecutionEngine(connector)
        self.schema_transformer = SchemaTransformer(connector.dialect)

    async def run(self, user_query: str) -> ExecutionTraceRecord:

        memory = ExecutionMemory(
            user_query=user_query,
            max_retries=MAX_REFLECTION_RETRIES,
        )

        memory.current_state = EngineState.INIT

        try:
            # ---------------- INIT → PLAN ----------------
            self._transition(memory, EngineState.PLAN)

            planner_context = ContextBuilder.build_for_planner(memory)
            plan_output = await self.planner_agent.run(planner_context)

            memory.planner_output = plan_output.model_dump()

            # ---------------- PLAN → SCHEMA_RETRIEVAL ----------------
            self._transition(memory, EngineState.SCHEMA_RETRIEVAL)

            raw_schema = await self.connector.introspect_schema()
            schema_context = self.schema_transformer.transform(raw_schema)

            memory.filtered_schema = schema_context.model_dump()

            # ---------------- SCHEMA → QUERY_GENERATION ----------------
            self._transition(memory, EngineState.QUERY_GENERATION)

            query_context = ContextBuilder.build_for_query(memory)
            query_output = await self.query_agent.run(query_context)

            memory.generated_sql = query_output.sql
            memory.confidence = query_output.confidence

            # ---------------- CRITIC ----------------
            critic_context = ContextBuilder.build_for_query(memory)
            critic_context.previous_sql = memory.generated_sql

            critic_output = await self.critic_agent.run(critic_context)
            memory.critic_output = critic_output.model_dump()

            # ---------------- VALIDATION ----------------
            self._transition(memory, EngineState.VALIDATION)

            if memory.generated_sql is None:
                raise ValueError("Error: generated_sql is None!")

            validation = self.policy_engine.enforce_readonly(memory.generated_sql)
            memory.validation_output = validation.model_dump()

            validated_sql = validation.normalized_sql

            # ---------------- EXECUTION ----------------
            self._transition(memory, EngineState.EXECUTION)

            if validated_sql is None:
                raise ValueError("Error: validated_sql is None!")

            execution_result: ExecutionResult = await self.execution_engine.execute(
                validated_sql
            )

            memory.execution_result = execution_result.model_dump()
            memory.execution_latency_ms = execution_result.elapsed_ms

            if execution_result.status == "success":
                self._transition(memory, EngineState.DONE)
                memory.final_state = EngineState.DONE
                return self._build_trace(memory)

            # ---------------- REFLECTION LOOP ----------------
            while execution_result.status != "success":

                memory.retry_count += 1

                if memory.retry_count > memory.max_retries:
                    self._transition(memory, EngineState.FAILED)
                    memory.final_state = EngineState.FAILED
                    return self._build_trace(memory)

                self._transition(memory, EngineState.REFLECTION)

                memory.last_error_message = (
                    execution_result.error_message or "Unknown execution error"
                )

                memory.reflection_history.append(
                    {
                        "previous_sql": memory.generated_sql,
                        "error_message": memory.last_error_message,
                    }
                )

                # REFLECTION → QUERY_GENERATION
                self._transition(memory, EngineState.QUERY_GENERATION)

                reflection_context = ContextBuilder.build_for_reflection(memory)
                query_output = await self.reflection_agent.run(reflection_context)

                memory.generated_sql = query_output.sql
                memory.confidence = query_output.confidence

                # CRITIC
                critic_context = ContextBuilder.build_for_query(memory)
                critic_context.previous_sql = memory.generated_sql

                critic_output = await self.critic_agent.run(critic_context)
                memory.critic_output = critic_output.model_dump()

                # VALIDATION
                self._transition(memory, EngineState.VALIDATION)

                if memory.generated_sql is None:
                    raise ValueError("Error: generated_sql is None!")

                validation = self.policy_engine.enforce_readonly(memory.generated_sql)
                memory.validation_output = validation.model_dump()

                validated_sql = validation.normalized_sql
                memory.reflection_history[-1]["corrected_sql"] = validated_sql

                # EXECUTION
                self._transition(memory, EngineState.EXECUTION)

                if validated_sql is None:
                    raise ValueError("Error: validated_sql is None!")

                execution_result = await self.execution_engine.execute(validated_sql)
                memory.execution_result = execution_result.model_dump()
                memory.execution_latency_ms = execution_result.elapsed_ms

                if execution_result.status == "success":
                    self._transition(memory, EngineState.DONE)
                    memory.final_state = EngineState.DONE
                    return self._build_trace(memory)

            # Fallback
            self._transition(memory, EngineState.FAILED)
            memory.final_state = EngineState.FAILED
            return self._build_trace(memory)

        except PolicyViolationError as e:
            memory.final_state = EngineState.FAILED
            memory.execution_result = {
                "status": "failed",
                "error_type": "policy_violation",
                "error_message": str(e),
            }
            return self._build_trace(memory)

        except Exception as e:
            memory.final_state = EngineState.FAILED
            memory.execution_result = {
                "status": "failed",
                "error_type": "controller_error",
                "error_message": str(e),
            }
            return self._build_trace(memory)

    # ---------------- INTERNAL HELPERS ----------------

    def _transition(self, memory: ExecutionMemory, next_state: EngineState):
        self.state_machine.validate_transition(
            EngineState(memory.current_state), next_state
        )
        memory.current_state = next_state

    def _build_trace(self, memory: ExecutionMemory) -> ExecutionTraceRecord:

        final_score, risk_penalty, critic_penalty, retry_penalty = _compute_score(
            model_confidence=memory.confidence or 0.0,
            validation_result=memory.validation_output,
            critic_result=memory.critic_output,
            retry_count=memory.retry_count,
        )

        return ExecutionTraceRecord(
            request_id=memory.request_id,
            user_query=memory.user_query,
            timestamp_iso=datetime.datetime.now(datetime.UTC).isoformat(),
            final_state=EngineState(memory.final_state),
            retry_count=memory.retry_count,
            plan=memory.planner_output,
            filtered_schema=memory.filtered_schema,
            generated_query=(
                {"sql": memory.generated_sql} if memory.generated_sql else None
            ),
            critic_result=memory.critic_output,
            validation_result=memory.validation_output,
            execution_result=memory.execution_result,
            execution_latency_ms=memory.execution_latency_ms,
            reflection_history=memory.reflection_history,
            final_confidence=memory.confidence,
            risk_penalty=risk_penalty,
            critic_penalty=critic_penalty,
            retry_penalty=retry_penalty,
            final_score=final_score,
        )
