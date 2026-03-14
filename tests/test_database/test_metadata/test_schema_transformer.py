from app.core.constants import DatabaseDialect
from app.database.metadata.schema_transformer import SchemaTransformer


def test_schema_transformer_basic():
    snapshot = {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "integer",
                        "is_nullable": False,
                    },
                    {
                        "name": "name",
                        "data_type": "text",
                        "is_nullable": True,
                    },
                ],
                "foreign_keys": [],
            }
        ]
    }

    transformer = SchemaTransformer(DatabaseDialect.POSTGRES)
    schema_context = transformer.transform(snapshot)

    assert schema_context.dialect == "POSTGRES"
    assert len(schema_context.tables) == 1
    assert schema_context.tables[0].name == "users"
    assert len(schema_context.tables[0].columns) == 2


def test_schema_transformer_foreign_keys():
    snapshot = {
        "tables": [
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "data_type": "integer", "is_nullable": False},
                    {"name": "user_id", "data_type": "integer", "is_nullable": False},
                ],
                "foreign_keys": [
                    {
                        "column": "user_id",
                        "ref_table": "users",
                        "ref_column": "id",
                    }
                ],
            }
        ]
    }

    transformer = SchemaTransformer(DatabaseDialect.POSTGRES)
    schema_context = transformer.transform(snapshot)

    table = schema_context.tables[0]

    assert table.foreign_keys[0].column == "user_id"
    assert table.foreign_keys[0].ref_table == "users"
