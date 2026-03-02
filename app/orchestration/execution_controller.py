import datetime

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


class ExecutionController:
    """Deterministic orchestrator - Owns the workflow"""

    def __init__(
        self,
        connector: BaseConnector,
        planner_agent: PlannerAgent,
        query_agent: QueryAgent,
        reflection_agent: ReflectionAgent,
    ) -> None:
        self.state_machine = StateMachine()
        self.connector = connector
        self.planner_agent = planner_agent
        self.query_agent = query_agent
        self.reflection_agent = reflection_agent

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

            # ----------------------------
            # Success Path
            # ----------------------------
            if execution_result.status == "success":
                self.state_machine.transition(EngineState.DONE)
                trace.state = EngineState.DONE
                trace.retry_count = self.state_machine.reflection_retries
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
