from abc import ABC, abstractmethod
from typing import Any

from app.core.constants import DatabaseDialect


class BaseConnector(ABC):
    """Abstract interface for all database connectors."""

    dialect: DatabaseDialect

    @abstractmethod
    async def connect(self) -> None:
        """Establish an connection with the DB"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close an existing connection with the DB"""
        ...

    @abstractmethod
    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """Execute validated SQL and return structured rows"""
        ...

    @abstractmethod
    async def introspect_schema(self) -> list[dict[str, Any]]:
        """Return raw schema snapshot (Deterministic)"""
        ...
