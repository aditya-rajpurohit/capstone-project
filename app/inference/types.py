from dataclasses import dataclass


@dataclass
class ModelRequest:
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int | None = None


@dataclass
class ModelResponse:
    raw_text: str
    provider: str
    model: str
