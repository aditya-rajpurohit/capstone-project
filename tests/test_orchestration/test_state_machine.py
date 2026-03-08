import pytest

from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.core.exceptions import InvalidStateTransitionError
from app.orchestration.state_machine import StateMachine


def test_valid_transitions():
    state_machine = StateMachine()

    # INIT
    assert state_machine.validate_transition(EngineState.INIT, EngineState.PLAN) == None
    assert (
        state_machine.validate_transition(EngineState.INIT, EngineState.FAILED) == None
    )

    # PLAN
    assert (
        state_machine.validate_transition(
            EngineState.PLAN, EngineState.SCHEMA_RETRIEVAL
        )
        == None
    )
    assert (
        state_machine.validate_transition(EngineState.PLAN, EngineState.FAILED) == None
    )

    # SCHEMA_RETRIEVAL
    assert (
        state_machine.validate_transition(
            EngineState.SCHEMA_RETRIEVAL, EngineState.QUERY_GENERATION
        )
        == None
    )
    assert (
        state_machine.validate_transition(
            EngineState.SCHEMA_RETRIEVAL, EngineState.FAILED
        )
        == None
    )

    # QUERY_GENERATION
    assert (
        state_machine.validate_transition(
            EngineState.QUERY_GENERATION, EngineState.VALIDATION
        )
        == None
    )
    assert (
        state_machine.validate_transition(
            EngineState.QUERY_GENERATION, EngineState.FAILED
        )
        == None
    )

    # VALIDATION
    assert (
        state_machine.validate_transition(EngineState.VALIDATION, EngineState.EXECUTION)
        == None
    )
    assert (
        state_machine.validate_transition(
            EngineState.VALIDATION, EngineState.REFLECTION
        )
        == None
    )
    assert (
        state_machine.validate_transition(EngineState.VALIDATION, EngineState.FAILED)
        == None
    )

    # EXECUTION
    assert (
        state_machine.validate_transition(EngineState.EXECUTION, EngineState.DONE)
        == None
    )
    assert (
        state_machine.validate_transition(EngineState.EXECUTION, EngineState.REFLECTION)
        == None
    )
    assert (
        state_machine.validate_transition(EngineState.EXECUTION, EngineState.FAILED)
        == None
    )

    # REFLECTION
    assert (
        state_machine.validate_transition(
            EngineState.REFLECTION, EngineState.QUERY_GENERATION
        )
        == None
    )
    assert (
        state_machine.validate_transition(EngineState.REFLECTION, EngineState.FAILED)
        == None
    )


def test_invalid_transition():
    state_machine = StateMachine()

    with pytest.raises(InvalidStateTransitionError):
        state_machine.validate_transition(EngineState.INIT, EngineState.EXECUTION)
