from unittest.mock import MagicMock
from app.engine.strategy.db_router import DBRouter
from app.database.registry.database_registry import DatabaseRegistry, DataSourceHandle
from app.core.constants import DatabaseDialect


def build_registry():
    registry = DatabaseRegistry()

    registry._handles = {
        "db1": DataSourceHandle(
            id="db1",
            name="analytics",
            dialect=DatabaseDialect.POSTGRES,
            connector=MagicMock(),
        ),
        "db2": DataSourceHandle(
            id="db2",
            name="warehouse",
            dialect=DatabaseDialect.POSTGRES,
            connector=MagicMock(),
        ),
        "db3": DataSourceHandle(
            id="db3",
            name="storage",
            dialect=DatabaseDialect.POSTGRES,
            connector=MagicMock(),
        ),
    }

    return registry


def test_db_router_match_by_name():
    registry = build_registry()

    routed = DBRouter.route(
        user_query="Query analytics database",
        active_database_ids=["db1", "db2"],
        registry=registry,
    )

    assert routed == ["db1"]


def test_db_router_match_by_id():
    registry = build_registry()

    routed = DBRouter.route(
        user_query="run query on db2",
        active_database_ids=["db1", "db2"],
        registry=registry,
    )

    assert routed == ["db2"]


def test_db_router_multiple_matches():
    registry = build_registry()

    routed = DBRouter.route(
        user_query="Query analytics and storage database",
        active_database_ids=["db1", "db3"],
        registry=registry,
    )

    assert routed == ["db1", "db3"]


def test_db_router_no_match_returns_all():
    registry = build_registry()

    routed = DBRouter.route(
        user_query="show all users",
        active_database_ids=["db1", "db2"],
        registry=registry,
    )

    assert routed == ["db1", "db2"]
