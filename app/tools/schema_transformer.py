from typing import Any

from app.core.constants import DatabaseDialect
from app.schemas.schema_context_schema import (ColumnInfo, ForeignKeyInfo,
                                               SchemaContext, TableInfo)


class SchemaTransformer:
    """Deterministic transformation: Raw DB snapshot → Structured SchemaContext model"""

    def __init__(self, dialect: DatabaseDialect) -> None:
        self.dialect = dialect

    def transform(self, raw_snapshot: list[dict[str, Any]]) -> SchemaContext:
        """Convert raw introspection output into SchemaContext"""

        tables: list[TableInfo] = []

        for table in raw_snapshot:
            table_name = table.get("table_name")
            if not table_name:
                continue

            columns_raw = table.get("columns", [])
            foreign_keys_raw = table.get("foreign_keys", [])

            columns: list[ColumnInfo] = [
                ColumnInfo(
                    name=col["column_name"],
                    data_type=col.get("data_type"),
                    is_nullable=(col.get("is_nullable") == "YES"),
                )
                for col in columns_raw
            ]

            foreign_keys: list[ForeignKeyInfo] = [
                ForeignKeyInfo(
                    column=fk["column_name"],
                    ref_table=fk["foreign_table_name"],
                    ref_column=fk["foreign_column_name"],
                )
                for fk in foreign_keys_raw
            ]

            tables.append(
                TableInfo(
                    name=table_name,
                    columns=columns,
                    foreign_keys=foreign_keys,
                )
            )

        return SchemaContext(dialect=self.dialect.value, tables=tables)
