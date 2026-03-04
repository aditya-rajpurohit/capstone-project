from dataclasses import dataclass
from typing import Set as set_type

from app.core.constants import EngineState
from app.core.exceptions import InvalidStateTransitionError

ALLOWED_TRANSITIONS: dict[EngineState, set_type[EngineState]] = {
    EngineState.INIT: {EngineState.PLAN, EngineState.FAILED},
    EngineState.PLAN: {EngineState.SCHEMA_RETRIEVAL, EngineState.FAILED},
    EngineState.SCHEMA_RETRIEVAL: {EngineState.QUERY_GENERATION, EngineState.FAILED},
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
    EngineState.REFLECTION: {EngineState.QUERY_GENERATION, EngineState.FAILED},
    EngineState.DONE: set(),
    EngineState.FAILED: set(),
}


@dataclass
class StateMachine:
    def validate_transition(
        self, from_state: EngineState, to_state: EngineState
    ) -> None:
        if to_state not in ALLOWED_TRANSITIONS.get(from_state, set()):
            raise InvalidStateTransitionError(
                f"Invalid transition: {from_state} -> {to_state}"
            )
