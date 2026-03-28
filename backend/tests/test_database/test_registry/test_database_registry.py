from unittest.mock import MagicMock, patch

import pytest

from app.core.constants import DatabaseDialect
from app.database.registry.database_registry import (DatabaseRegistry,
                                                     DataSourceHandle)


def test_database_registry_singleton():
    DatabaseRegistry._instance = None
    r1 = DatabaseRegistry.get_instance()
    r2 = DatabaseRegistry.get_instance()

    assert r1 is r2


def test_registry_get_and_list():
    registry = DatabaseRegistry()

    handle = DataSourceHandle(
        id="db1",
        name="test",
        dialect=DatabaseDialect.POSTGRES,
        connector=MagicMock(),
    )

    registry._handles["db1"] = handle

    assert registry.get("db1") == handle
    assert registry.list_all() == [handle]


def test_registry_list_healthy():
    registry = DatabaseRegistry()

    healthy = DataSourceHandle(
        id="h",
        name="healthy",
        dialect=DatabaseDialect.POSTGRES,
        connector=MagicMock(),
        is_active=True,
        is_healthy=True,
    )

    unhealthy = DataSourceHandle(
        id="u",
        name="unhealthy",
        dialect=DatabaseDialect.POSTGRES,
        connector=MagicMock(),
        is_active=True,
        is_healthy=False,
    )

    registry._handles = {"h": healthy, "u": unhealthy}

    result = registry.list_healthy()

    assert result == [healthy]


def test_mark_unhealthy():
    registry = DatabaseRegistry()

    handle = DataSourceHandle(
        id="db1",
        name="test",
        dialect=DatabaseDialect.POSTGRES,
        connector=MagicMock(),
    )

    registry._handles["db1"] = handle

    registry.mark_unhealthy("db1")

    assert handle.is_healthy is False


def test_parse_dialect_from_string():
    registry = DatabaseRegistry()

    result = registry._parse_dialect("postgres")

    assert result == DatabaseDialect.POSTGRES


def test_parse_dialect_enum_passthrough():
    registry = DatabaseRegistry()

    result = registry._parse_dialect(DatabaseDialect.POSTGRES)

    assert result == DatabaseDialect.POSTGRES


def test_build_connector_postgres():
    registry = DatabaseRegistry()

    row = MagicMock()
    row.username = "u"
    row.encrypted_password = "p"
    row.host = "localhost"
    row.port = 5432
    row.database_name = "db"

    with patch(
        "app.database.registry.database_registry.PostgresConnector"
    ) as mock_connector:

        registry._build_connector(row, DatabaseDialect.POSTGRES)

        mock_connector.assert_called_once()
