from dataclasses import dataclass

from app.tools.db_connector.base_connector import BaseConnector


@dataclass
class DBUnit:
    id: str
    dialect: str
    connector: BaseConnector
    is_healthy: bool = True


class DatabaseRegistry:

    _instance = None

    def __init__(self) -> None:
        self._db_units: dict[str, DBUnit] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, db_unit: DBUnit):
        self._db_units[db_unit.id] = db_unit

    def get(self, db_id: str) -> DBUnit | None:
        return self._db_units.get(db_id)

    def list_all(self) -> list[DBUnit]:
        return list(self._db_units.values())

    def mark_unhealthy(self, db_id: str) -> None:
        if db_id in self._db_units:
            self._db_units[db_id].is_healthy = False

    def list_healthy(self) -> list[DBUnit]:
        return [
            db for db in self._db_units.values()
            if db.is_healthy
        ]
