from dataclasses import dataclass

from app.core.constants import EngineState


@dataclass(frozen=True)
class Transition:
    from_state: EngineState
    to_state: EngineState
    reason: str | None = None
