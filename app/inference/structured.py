import json
from typing import TypeVar

from pydantic import BaseModel

from app.inference.base import Model
from app.inference.types import ModelRequest
from app.orchestration.structured_validator import validate_contract

T = TypeVar("T", bound=BaseModel)


class StructuredModel:
    """Wraps model output with strict schema validation"""

    def __init__(self, model: Model) -> None:
        self.model = model

    async def generate(self, request: ModelRequest, schema: type[T]) -> T:
        response = await self.model.generate(request=request, schema=schema)

        try:
            raw_text = response.raw_text.strip()
            parsed_response = json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError("Model did not return valid JSON.")

        # provider to return JSON string
        return validate_contract(schema, parsed_response)
