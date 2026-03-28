from typing import Any

from app.core.constants import DatabaseDialect
from app.engine.contracts.schema_context_contract import (ColumnInfo,
                                                          ForeignKeyInfo,
                                                          SchemaContext,
                                                          TableInfo)


class SchemaTransformer:
    """Deterministic transformation: Raw DB snapshot → Structured SchemaContext model"""

    def __init__(self, dialect: DatabaseDialect) -> None:
        self.dialect = dialect

    def transform(self, snapshot: dict[str, Any]) -> SchemaContext:
        """
        Convert stored schema snapshot into SchemaContext.
        Snapshot must already be normalized.
        """
        tables: list[TableInfo] = []

        for table in snapshot.get("tables", []):
            columns = [
                ColumnInfo(
                    name=col["name"],
                    data_type=col.get("data_type"),
                    is_nullable=col.get("is_nullable"),
                )
                for col in table.get("columns", [])
            ]

            foreign_keys = [
                ForeignKeyInfo(
                    column=fk["column"],
                    ref_table=fk["ref_table"],
                    ref_column=fk["ref_column"],
                )
                for fk in table.get("foreign_keys", [])
            ]

            tables.append(
                TableInfo(
                    name=table["name"],
                    columns=columns,
                    foreign_keys=foreign_keys,
                )
            )

        return SchemaContext(dialect=self.dialect.value, tables=tables)
