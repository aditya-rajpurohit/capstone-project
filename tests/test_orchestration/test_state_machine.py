import pytest

from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
from app.core.exceptions import InvalidStateTransitionError
from app.orchestration.state_machine import StateMachine


def test_valid_transitions_happy_path():
    sm = StateMachine()

    sm.transition(EngineState.PLAN)
    sm.transition(EngineState.SCHEMA_RETRIEVAL)
    sm.transition(EngineState.QUERY_GENERATION)
    sm.transition(EngineState.VALIDATION)
    sm.transition(EngineState.EXECUTION)
    sm.transition(EngineState.DONE)

    assert sm.state == EngineState.DONE


def test_invalid_transition_rejected():
    sm = StateMachine()

    with pytest.raises(InvalidStateTransitionError):
        sm.transition(EngineState.EXECUTION)


def test_reflection_retry_cap_forces_failed():
    sm = StateMachine(state=EngineState.VALIDATION)

    # transition into reflection MAX+1 times via allowed path simulation
    for _ in range(MAX_REFLECTION_RETRIES):
        sm.transition(EngineState.REFLECTION)

        assert sm.state == EngineState.REFLECTION

        sm.transition(EngineState.QUERY_GENERATION)
        sm.transition(EngineState.VALIDATION)

    # next reflection should force FAILED
    sm.transition(EngineState.REFLECTION)

    assert sm.state == EngineState.FAILED
