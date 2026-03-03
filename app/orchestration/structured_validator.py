from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.exceptions import ContractValidationError

T = TypeVar("T", bound=BaseModel)


def validate_contract(model: Type[T], payload: Any) -> T:
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
