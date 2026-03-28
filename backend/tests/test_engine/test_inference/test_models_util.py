from app.engine.inference.models_util import openai_schema


def test_openai_schema_enforces_required_and_additional_properties():
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer"},
        },
    }

    result = openai_schema(schema)

    assert result["required"] == ["name", "count"]
    assert result["additionalProperties"] is False


def test_openai_schema_resolves_refs():
    schema = {
        "type": "object",
        "properties": {"item": {"$ref": "#/$defs/Item"}},
        "$defs": {
            "Item": {"type": "object", "properties": {"id": {"type": "integer"}}}
        },
    }

    result = openai_schema(schema)

    assert "$defs" not in result
    assert result["properties"]["item"]["type"] == "object"
    assert result["properties"]["item"]["required"] == ["id"]
    assert result["properties"]["item"]["additionalProperties"] is False


def test_openai_schema_enforces_array_items():
    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "integer"}},
                },
            }
        },
    }

    result = openai_schema(schema)

    item_schema = result["properties"]["items"]["items"]
    assert item_schema["required"] == ["id"]
    assert item_schema["additionalProperties"] is False
