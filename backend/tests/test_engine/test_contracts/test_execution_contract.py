from app.engine.contracts.execution_contract import ExecutionResult


def test_execution_result():
    result = ExecutionResult(status="success", rows=[{"id": 1}], row_count=1)

    assert result.status == "success"
    assert result.row_count == 1
