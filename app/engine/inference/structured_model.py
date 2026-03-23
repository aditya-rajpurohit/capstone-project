import json
import re
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.exceptions import ContractValidationError
from app.engine.inference.base import Model
from app.engine.inference.types import ModelRequest

T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> str:
    text = text.strip()

    # Remove ```json fences
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    return text.strip()


def _validate_contract(model: Type[T], payload: Any) -> T:
    """
    Strict validation.
    Iteration 1 policy:
      - No repair loop
      - Validation errors => hard fail
    """
    try:
        return model.model_validate(payload)
    except ValidationError as e:
        raise ContractValidationError(str(e)) from e


class StructuredModel:
    """Wraps model output with strict schema validation"""

    def __init__(self, model: Model) -> None:
        self.model = model

    async def generate(
        self, request: ModelRequest, schema: Optional[type[T]] = None
    ) -> T | str:
        response = await self.model.generate(request=request, schema=schema)

        raw_text = _extract_json(response.raw_text)

        if schema is None:
            return raw_text

        try:
            parsed_response = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise ContractValidationError(
                "ERROR: Model did not return valid JSON"
            ) from e

        # provider to return JSON string
        return _validate_contract(schema, parsed_response)
