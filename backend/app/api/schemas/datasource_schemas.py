from pydantic import BaseModel, Field


class PostgresConfig(BaseModel):
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str


class RegisterDatasourceRequest(BaseModel):
    name: str
    dialect: str = Field(..., description="postgres")
    config: PostgresConfig


class DatasourceResponse(BaseModel):
    id: str
    name: str
    dialect: str
    is_active: bool
    is_healthy: bool
    created_at: str
