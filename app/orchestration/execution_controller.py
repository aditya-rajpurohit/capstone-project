import datetime
from app.core.constants import EngineState
from app.core.exceptions import PolicyViolationError
from app.orchestration.state_machine import StateMachine
from app.orchestration.policy_engine import SQLPolicyEngine
from app.tools.schema_transformer import SchemaTransformer
from app.tools.execution_engine import ExecutionEngine
from app.schemas.execution_schema import ExecutionResult
from app.schemas.trace_schema import ExecutionTraceRecord


class ExecutionController:
    """Deterministic orchestrator - Owns the workflow"""

    def __init__(self, connector) -> None:
        self.state_machine = StateMachine()
        self.connector = connector
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
            # INIT → PLAN
            self.state_machine.transition(EngineState.PLAN)

            # MOCK Planner
            plan = {
                "intent": "list",
                "operation": "SELECT",
                "entities": [],
                "constraints": [],
                "confidence": 1.0,
            }
            trace.plan = plan

            # PLAN → SCHEMA_RETRIEVAL
            self.state_machine.transition(EngineState.SCHEMA_RETRIEVAL)

            raw_schema = await self.connector.introspect_schema()
            schema_context = self.schema_transformer.transform(raw_schema)
            trace.schema_context = schema_context.model_dump()

            # SCHEMA_RETRIEVAL → QUERY_GENERATION
            self.state_machine.transition(EngineState.QUERY_GENERATION)

            # MOCK Query Agent
            generated_sql = "SELECT * FROM users"
            trace.generated_query = {
                "sql": generated_sql,
                "confidence": 1.0,
            }

            # QUERY_GENERATION → VALIDATION
            self.state_machine.transition(EngineState.VALIDATION)

            validated_sql = self.policy_engine.enforce_readonly(generated_sql)

            # VALIDATION → EXECUTION
            self.state_machine.transition(EngineState.EXECUTION)

            execution_result: ExecutionResult = await self.execution_engine.execute(validated_sql)
            trace.execution_result = execution_result.model_dump()

            if execution_result.status == "success":
                self.state_machine.transition(EngineState.DONE)
                trace.state = EngineState.DONE
            else:
                self.state_machine.transition(EngineState.FAILED)
                trace.state = EngineState.FAILED

            trace.final_confidence = 1.0
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
        