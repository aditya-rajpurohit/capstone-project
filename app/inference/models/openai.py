import os
from typing import Type, cast

from openai import NOT_GIVEN, AsyncOpenAI
from openai.types.chat.completion_create_params import ResponseFormat
from openai.types.shared_params.response_format_json_schema import (
    JSONSchema, ResponseFormatJSONSchema)
from pydantic import BaseModel

from app.inference.base import Model
from app.inference.schema_util import openai_schema
from app.inference.types import ModelRequest, ModelResponse

_KEY = os.getenv("OPENAI_API_KEY")


class OpenAI(Model):

    def __init__(self) -> None:
        if not _KEY:
            raise ValueError("Error: OPENAI_API_KEY not assigned!")
        self.client = AsyncOpenAI(api_key=_KEY)

    async def generate(
        self, request: ModelRequest, schema: Type[BaseModel] | None = None
    ) -> ModelResponse:

        response_format: ResponseFormat | object = NOT_GIVEN

        if schema is None:
            response_format = NOT_GIVEN
        else:
            raw_schema = schema.model_json_schema()
            strict_schema = openai_schema(raw_schema)

            response_format = ResponseFormatJSONSchema(
                type="json_schema",
                json_schema=JSONSchema(
                    name=schema.__name__,
                    schema=strict_schema,
                    strict=True,
                ),
            )

        response_format = cast(ResponseFormat, response_format)

        response = await self.client.chat.completions.create(
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            response_format=response_format,
        )

        if not response.choices[0].message.content:
            raise ValueError("OpenAI response error!")

        return ModelResponse(
            raw_text=response.choices[0].message.content or "",
            provider="openai",
            model=request.model,
        )
