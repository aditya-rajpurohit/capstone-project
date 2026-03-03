import datetime

from app.agents.critic_agent import CriticAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent
from app.agents.reflection_agent import ReflectionAgent
from app.core.constants import EngineState
from app.core.exceptions import PolicyViolationError
from app.orchestration.policy_engine import SQLPolicyEngine
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
    # Policy risk penalty
    risk_penalty = 0.0
    if validation_result:
        if validation_result.get("risk_level") == "medium":
            risk_penalty = 0.1
        elif validation_result.get("risk_level") == "high":
            risk_penalty = 0.2

    # Critic penalty
    critic_penalty = 0.0
    if critic_result:
        if critic_result.get("risk_level") == "medium":
            critic_penalty = 0.1
        elif critic_result.get("risk_level") == "high":
            critic_penalty = 0.2

    # Retry penalty
    retry_penalty = retry_count * 0.05

    final_score = max(
        0.0,
        model_confidence - risk_penalty - critic_penalty - retry_penalty,
    )

    return final_score, risk_penalty, critic_penalty, retry_penalty


class ExecutionController:
    """Deterministic orchestrator - Owns the workflow"""

    def __init__(
        self,
        connector: BaseConnector,
        planner_agent: PlannerAgent,
        query_agent: QueryAgent,
        reflection_agent: ReflectionAgent,
        critic_agent: CriticAgent,
    ) -> None:
        self.state_machine = StateMachine()
        self.connector = connector
        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent
        self.critic_agent = critic_agent

        self.policy_engine = SQLPolicyEngine(dialect=connector.dialect)
        self.execution_engine = ExecutionEngine(connector)
        self.schema_transformer = SchemaTransformer(connector.dialect)

    async def run(self, user_query: str) -> ExecutionTraceRecord:

        trace = ExecutionTraceRecord(
            user_query=user_query,
            state=self.state_machine.state,
            retry_count=0,
            timestamp_iso=datetime.datetime.now(datetime.UTC).isoformat(),
        )

        try:
            # ----------------------------
            # INIT → PLAN
            # ----------------------------
            self.state_machine.transition(EngineState.PLAN)

            plan = await self.planner_agent.run(user_query)
            trace.plan = plan.model_dump()

            # ----------------------------
            # PLAN → SCHEMA_RETRIEVAL
            # ----------------------------
            self.state_machine.transition(EngineState.SCHEMA_RETRIEVAL)

            raw_schema = await self.connector.introspect_schema()
            schema_context = self.schema_transformer.transform(raw_schema)
            trace.schema_context = schema_context.model_dump()

            # ----------------------------
            # First Query Generation
            # ----------------------------
            self.state_machine.transition(EngineState.QUERY_GENERATION)

            query_output = await self.query_agent.run(plan, schema_context)
            trace.generated_query = query_output.model_dump()

            # ----------------------------
            # Critic Agent
            # ----------------------------
            critic_output = await self.critic_agent.run(query_output, schema_context)
            trace.critic_result = critic_output.model_dump()

            # ----------------------------
            # Validation
            # ----------------------------
            self.state_machine.transition(EngineState.VALIDATION)

            validation = self.policy_engine.enforce_readonly(query_output.sql)
            trace.validation_result = validation.model_dump()
            assert validation.normalized_sql is not None, "Validation produced no SQL."
            validated_sql = validation.normalized_sql

            # ----------------------------
            # Execution
            # ----------------------------
            self.state_machine.transition(EngineState.EXECUTION)

            execution_result: ExecutionResult = await self.execution_engine.execute(
                validated_sql
            )
            trace.execution_result = execution_result.model_dump()
            trace.execution_latency_ms = execution_result.elapsed_ms

            # ----------------------------
            # Success Path
            # ----------------------------
            if execution_result.status == "success":
                self.state_machine.transition(EngineState.DONE)
                trace.state = EngineState.DONE
                trace.retry_count = self.state_machine.reflection_retries
                trace.execution_latency_ms = execution_result.elapsed_ms

                final_score, risk_penalty, critic_penalty, retry_penalty = (
                    _compute_score(
                        model_confidence=query_output.confidence,
                        validation_result=trace.validation_result,
                        critic_result=trace.critic_result,
                        retry_count=trace.retry_count,
                    )
                )

                trace.risk_penalty = risk_penalty
                trace.critic_penalty = critic_penalty
                trace.retry_penalty = retry_penalty
                trace.final_score = final_score
                trace.final_confidence = query_output.confidence

                return trace

            # ----------------------------
            # Reflection Path
            # ----------------------------
            while execution_result.status != "success":

                # Move to reflection
                self.state_machine.transition(EngineState.REFLECTION)

                # Retry cap reached → fail
                if self.state_machine.state == EngineState.FAILED:
                    trace.state = EngineState.FAILED
                    trace.retry_count = self.state_machine.reflection_retries
                    return trace

                error_message = (
                    execution_result.error_message or "Unknown execution error"
                )

                # Record reflection attempt
                trace.reflection_history.append(
                    {
                        "previous_sql": validated_sql,
                        "error_message": error_message,
                    }
                )

                # REFLECTION → QUERY_GENERATION
                self.state_machine.transition(EngineState.QUERY_GENERATION)

                query_output = await self.reflection_agent.run(
                    plan,
                    schema_context,
                    previous_sql=validated_sql,
                    error_message=error_message,
                )

                trace.generated_query = query_output.model_dump()

                # CRITIC AGENT
                critic_output = await self.critic_agent.run(
                    query_output, schema_context
                )
                trace.critic_result = critic_output.model_dump()

                # QUERY_GENERATION → VALIDATION
                self.state_machine.transition(EngineState.VALIDATION)

                validation = self.policy_engine.enforce_readonly(query_output.sql)
                trace.validation_result = validation.model_dump()
                assert (
                    validation.normalized_sql is not None
                ), "Validation produced no SQL."
                validated_sql = validation.normalized_sql

                # Record corrected SQL
                trace.reflection_history[-1]["corrected_sql"] = validated_sql

                # VALIDATION → EXECUTION
                self.state_machine.transition(EngineState.EXECUTION)

                execution_result = await self.execution_engine.execute(validated_sql)
                trace.execution_result = execution_result.model_dump()

                if execution_result.status == "success":
                    self.state_machine.transition(EngineState.DONE)
                    trace.state = EngineState.DONE
                    trace.retry_count = self.state_machine.reflection_retries
                    trace.final_confidence = query_output.confidence
                    return trace

            # Fallback
            self.state_machine.transition(EngineState.FAILED)
            trace.state = EngineState.FAILED
            trace.retry_count = self.state_machine.reflection_retries

            return trace

        except PolicyViolationError as e:
            self.state_machine.transition(EngineState.FAILED)
            trace.state = EngineState.FAILED
            trace.execution_result = {
                "status": "failed",
                "error_type": "policy_violation",
                "error_message": str(e),
            }

            return trace

        except Exception as e:
            self.state_machine.transition(EngineState.FAILED)
            trace.state = EngineState.FAILED
            trace.execution_result = {
                "status": "failed",
                "error_type": "controller_error",
                "error_message": str(e),
            }

            return trace
