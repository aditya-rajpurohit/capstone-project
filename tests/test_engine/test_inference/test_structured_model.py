from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from app.core.exceptions import ContractValidationError
from app.engine.inference.structured_model import (StructuredModel,
                                                   _extract_json,
                                                   _validate_contract)
from app.engine.inference.types import ModelRequest, ModelResponse


class DummySchema(BaseModel):
    name: str
    count: int


def test_extract_json_plain_text():
    text = '{"name": "x", "count": 1}'

    result = _extract_json(text)

    assert result == '{"name": "x", "count": 1}'


def test_extract_json_removes_code_fence():
    text = '```json\n{"name": "x", "count": 1}\n```'

    result = _extract_json(text)

    assert result == '{"name": "x", "count": 1}'


def test_validate_contract_success():
    result = _validate_contract(DummySchema, {"name": "x", "count": 1})

    assert result.name == "x"
    assert result.count == 1


def test_validate_contract_failure():
    with pytest.raises(ContractValidationError):
        _validate_contract(DummySchema, {"name": "x", "count": "bad"})


@pytest.mark.asyncio
async def test_structured_model_generate_without_schema_returns_text():
    model = AsyncMock()
    model.generate.return_value = ModelResponse(
        raw_text="```json\nhello\n```",
        provider="openai",
        model="gpt",
    )

    structured = StructuredModel(model)

    request = ModelRequest(
        system_prompt="sys",
        user_prompt="user",
        model="gpt",
    )

    result = await structured.generate(request)

    assert result == "hello"


@pytest.mark.asyncio
async def test_structured_model_generate_with_schema_success():
    model = AsyncMock()
    model.generate.return_value = ModelResponse(
        raw_text='{"name": "x", "count": 1}',
        provider="openai",
        model="gpt",
    )

    structured = StructuredModel(model)

    request = ModelRequest(
        system_prompt="sys",
        user_prompt="user",
        model="gpt",
    )

    result = await structured.generate(request, DummySchema)

    assert isinstance(result, DummySchema)
    assert result.name == "x"
    assert result.count == 1


@pytest.mark.asyncio
async def test_structured_model_generate_invalid_json():
    model = AsyncMock()
    model.generate.return_value = ModelResponse(
        raw_text="not json",
        provider="openai",
        model="gpt",
    )

    structured = StructuredModel(model)

    request = ModelRequest(
        system_prompt="sys",
        user_prompt="user",
        model="gpt",
    )

    with pytest.raises(ContractValidationError, match="valid JSON"):
        await structured.generate(request, DummySchema)


@pytest.mark.asyncio
async def test_structured_model_generate_invalid_schema():
    model = AsyncMock()
    model.generate.return_value = ModelResponse(
        raw_text='{"name": "x", "count": "bad"}',
        provider="openai",
        model="gpt",
    )

    structured = StructuredModel(model)

    request = ModelRequest(
        system_prompt="sys",
        user_prompt="user",
        model="gpt",
    )

    with pytest.raises(ContractValidationError):
        await structured.generate(request, DummySchema)
