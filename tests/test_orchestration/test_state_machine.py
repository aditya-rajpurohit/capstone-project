import pytest

from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.core.exceptions import InvalidStateTransitionError
from app.orchestration.state_machine import StateMachine


def test_valid_transitions():
    sm = StateMachine()

    # INIT
    assert sm.validate_transition(EngineState.INIT, EngineState.PLAN) == None
    assert sm.validate_transition(EngineState.INIT, EngineState.FAILED) == None

    # PLAN
    assert (
        sm.validate_transition(EngineState.PLAN, EngineState.SCHEMA_RETRIEVAL) == None
    )
    assert sm.validate_transition(EngineState.PLAN, EngineState.FAILED) == None

    # SCHEMA_RETRIEVAL
    assert (
        sm.validate_transition(
            EngineState.SCHEMA_RETRIEVAL, EngineState.QUERY_GENERATION
        )
        == None
    )
    assert (
        sm.validate_transition(EngineState.SCHEMA_RETRIEVAL, EngineState.FAILED) == None
    )

    # QUERY_GENERATION
    assert (
        sm.validate_transition(EngineState.QUERY_GENERATION, EngineState.VALIDATION)
        == None
    )
    assert (
        sm.validate_transition(EngineState.QUERY_GENERATION, EngineState.FAILED) == None
    )

    # VALIDATION
    assert sm.validate_transition(EngineState.VALIDATION, EngineState.EXECUTION) == None
    assert (
        sm.validate_transition(EngineState.VALIDATION, EngineState.REFLECTION) == None
    )
    assert sm.validate_transition(EngineState.VALIDATION, EngineState.FAILED) == None

    # EXECUTION
    assert sm.validate_transition(EngineState.EXECUTION, EngineState.DONE) == None
    assert sm.validate_transition(EngineState.EXECUTION, EngineState.REFLECTION) == None
    assert sm.validate_transition(EngineState.EXECUTION, EngineState.FAILED) == None

    # REFLECTION
    assert (
        sm.validate_transition(EngineState.REFLECTION, EngineState.QUERY_GENERATION)
        == None
    )
    assert sm.validate_transition(EngineState.REFLECTION, EngineState.FAILED) == None


def test_invalid_transition():
    sm = StateMachine()

    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(EngineState.INIT, EngineState.REFLECTION)
