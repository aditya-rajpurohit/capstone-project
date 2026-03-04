import uuid

from app.tools.db_connector.base_connector import BaseConnector


class DBUnit:
    def __init__(
        self,
        db_id: str,
        db_type: str,
        connector: BaseConnector,
        metadata: dict,
    ):
        self.db_id = db_id
        self.db_type = db_type
        self.connector = connector
        self.metadata = metadata
        self.is_healthy = True


class DatabaseRegistry:
    _instance = None

    def __init__(self):
        self._db_units: dict[str, DBUnit] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, db_unit: DBUnit):
        self._db_units[db_unit.db_id] = db_unit

    def get(self, db_id: str) -> DBUnit | None:
        return self._db_units.get(db_id)

    def list_all(self) -> list[DBUnit]:
        return list(self._db_units.values())

    def list_healthy(self) -> list[DBUnit]:
        return [db for db in self._db_units.values() if db.is_healthy]

    def mark_unhealthy(self, db_id: str):
        if db_id in self._db_units:
            self._db_units[db_id].is_healthy = False

    def remove(self, db_id: str):
        if db_id in self._db_units:
            del self._db_units[db_id]
