from app.strategy.db_router import DBRouter


class MockDB:
    def __init__(self, name):
        self.name = name


class MockRegistry:
    def __init__(self):
        self._units = {
            "db1": MockDB(name="analytics"),
            "db2": MockDB(name="warehouse"),
            "db3": MockDB(name="storage"),
        }

    def get(self, db_id):
        return self._units.get(db_id)


def test_db_router():
    # using regex on user_query to analyze which db_schema required based on active_databases
    registry = MockRegistry()

    routed = DBRouter.route(
        user_query="Query analytics & storage database",
        active_database_ids=["db1", "db3"],
        registry=registry,
    )

    assert routed == ["db1", "db3"]
