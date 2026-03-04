import pytest

from app.core.constants import DatabaseDialect
from app.tools.schema_transformer import SchemaTransformer


def test_schema_transformer_basic():
    raw_snapshot = [
        {
            "table_name": "users",
            "columns": [
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "is_nullable": "NO",
                },
                {
                    "column_name": "name",
                    "data_type": "text",
                    "is_nullable": "YES",
                },
            ],
            "foreign_keys": [],
        }
    ]

    transformer = SchemaTransformer(DatabaseDialect.POSTGRES)
    schema_context = transformer.transform(raw_snapshot)

    assert schema_context.dialect == "POSTGRES"
    assert len(schema_context.tables) == 1
    assert schema_context.tables[0].name == "users"
    assert len(schema_context.tables[0].columns) == 2
