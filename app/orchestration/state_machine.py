from dataclasses import dataclass
from typing import Set as set_type

from app.core.constants import MAX_REFLECTION_RETRIES, EngineState
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
    state: EngineState = EngineState.INIT
    reflection_retries: int = 0

    def can_transition(self, to_state: EngineState) -> bool:
        return to_state in ALLOWED_TRANSITIONS.get(self.state, set())

    def transition(self, to_state: EngineState) -> None:
        if not self.can_transition(to_state):
            raise InvalidStateTransitionError(
                f"Invalid transition: {self.state} -> {to_state}"
            )

        if to_state == EngineState.REFLECTION:
            if self.reflection_retries >= MAX_REFLECTION_RETRIES:
                self.state = EngineState.FAILED
                return
            self.reflection_retries += 1

        self.state = to_state
