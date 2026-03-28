from app.core.constants import EngineState
from app.engine.contracts.trace_schema import ExecutionTraceRecord


def test_execution_trace_record():
    record = ExecutionTraceRecord(
        request_id="1",
        user_query="test",
        timestamp_iso="2025-01-01T00:00:00Z",
        final_state=EngineState.DONE,
    )

    assert record.request_id == "1"
    assert record.final_state == EngineState.DONE
