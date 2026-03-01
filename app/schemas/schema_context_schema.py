from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    data_type: str | None = None
    is_nullable: bool | None = None


class ForeignKeyInfo(BaseModel):
    column: str
    ref_table: str
    ref_column: str


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo] = Field(default_factory=lambda: [])
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=lambda: [])


class SchemaContext(BaseModel):
    dialect: str
    tables: list[TableInfo] = Field(default_factory=lambda: [])
    confidence: float = Field(..., ge=0.0, le=1.0)
