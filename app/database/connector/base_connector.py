from abc import ABC, abstractmethod
from typing import Any

from app.core.constants import DatabaseDialect


class BaseConnector(ABC):
    """
    Abstract interface for database connectors.
    Connectors are responsible ONLY for:
    - Connection lifecycle
    - Raw query execution
    - Schema introspection
    """

    dialect: DatabaseDialect

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection or initialize pool."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connection or pool."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Lightweight health probe (SELECT 1 or equivalent)."""
        ...

    @abstractmethod
    async def execute(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL and return rows as list of dict."""
        ...

    @abstractmethod
    async def introspect_schema(self) -> dict[str, Any]:
        """
        Return normalized schema snapshot in canonical format:
        {
            "tables": [...]
        }
        """
        ...
