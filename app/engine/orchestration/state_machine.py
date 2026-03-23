from typing import Set

from app.core.constants import EngineState
from app.core.exceptions import InvalidStateTransitionError

ALLOWED_TRANSITIONS: dict[EngineState, Set[EngineState]] = {
    EngineState.INIT: {EngineState.PLAN, EngineState.FAILED},
    EngineState.PLAN: {EngineState.QUERY_GENERATION, EngineState.FAILED},
    EngineState.QUERY_GENERATION: {EngineState.VALIDATION, EngineState.FAILED},
    EngineState.VALIDATION: {
        EngineState.EXECUTION,
        EngineState.REFLECTION,
        EngineState.FAILED,
    },
    EngineState.EXECUTION: {
        EngineState.DONE,
        EngineState.REFLECTION,
        EngineState.FAILED,
    },
    EngineState.REFLECTION: {
        EngineState.QUERY_GENERATION,
        EngineState.FAILED,
    },
    EngineState.DONE: set(),
    EngineState.FAILED: set(),
}


class StateMachine:
    """
    Stateless transition validator.
    ExecutionMemory holds current state.
    """

    @staticmethod
    def validate_transition(from_state: EngineState, to_state: EngineState) -> None:

        allowed = ALLOWED_TRANSITIONS.get(from_state, set())

        if to_state not in allowed:
            raise InvalidStateTransitionError(
                f"ERROR: Invalid transition: {from_state} -> {to_state}!"
            )
