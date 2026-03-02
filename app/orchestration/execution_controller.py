import datetime
from app.agents.planner_agent import PlannerAgent
from app.agents.query_agent import QueryAgent
from app.core.constants import EngineState
from app.core.exceptions import PolicyViolationError
from app.orchestration.state_machine import StateMachine
from app.orchestration.policy_engine import SQLPolicyEngine
from app.tools.db_connector.base_connector import BaseConnector
from app.tools.schema_transformer import SchemaTransformer
from app.tools.execution_engine import ExecutionEngine
from app.schemas.execution_schema import ExecutionResult
from app.schemas.trace_schema import ExecutionTraceRecord


class ExecutionController:
    """Deterministic orchestrator - Owns the workflow"""

    def __init__(self, connector: BaseConnector, planner_agent: PlannerAgent, query_agent: QueryAgent) -> None:
        self.state_machine = StateMachine()
        self.connector = connector
        self.planner_agent = planner_agent
        self.query_agent = query_agent

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
            plan = await self.planner_agent.run(user_query)
            trace.plan = plan.model_dump()

            # PLAN → SCHEMA_RETRIEVAL
            self.state_machine.transition(EngineState.SCHEMA_RETRIEVAL)

            raw_schema = await self.connector.introspect_schema()
            schema_context = self.schema_transformer.transform(raw_schema)
            trace.schema_context = schema_context.model_dump()

            # SCHEMA_RETRIEVAL → QUERY_GENERATION
            self.state_machine.transition(EngineState.QUERY_GENERATION)

            # MOCK Query Agent
            query_output = await self.query_agent.run(plan, schema_context)
            trace.generated_query = query_output.model_dump()

            # QUERY_GENERATION → VALIDATION
            self.state_machine.transition(EngineState.VALIDATION)
            validated_sql = self.policy_engine.enforce_readonly(query_output.sql)

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

            trace.retry_count = self.state_machine.reflection_retries
            trace.final_confidence = query_output.confidence

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
            # Safety fallback
            self.state_machine.transition(EngineState.FAILED)
            trace.state = EngineState.FAILED
            trace.execution_result = {
                "status": "failed",
                "error_type": "controller_error",
                "error_message": str(e),
            }
            
            return trace
        