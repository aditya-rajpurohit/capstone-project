import pytest
from app.core.exceptions import (ContractValidationError, AgenticEngineError, InvalidStateTransitionError, PolicyViolationError, DataSourceExecutionError)


def test_agentic_engine_error():
    with pytest.raises(AgenticEngineError):
        raise AgenticEngineError("Invalid")


def test_contract_validation_error():
    with pytest.raises(ContractValidationError):
        raise ContractValidationError("Invalid")


def test_invalid_state_transition_error():
    with pytest.raises(InvalidStateTransitionError):
        raise InvalidStateTransitionError("Invalid")


def test_policy_violation_error():
    with pytest.raises(PolicyViolationError):
        raise PolicyViolationError("Invalid")


def test_datasource_execution_error():
    with pytest.raises(DataSourceExecutionError):
        raise DataSourceExecutionError("Invalid")
