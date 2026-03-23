from app.engine.context.schema_selector import SchemaSelector


def test_schema_selector_filters_relevant_tables():

    snapshot = {
        "tables": [
            {
                "name": "users",
                "columns": [{"name": "id"}, {"name": "name"}],
                "foreign_keys": [],
            },
            {
                "name": "orders",
                "columns": [{"name": "order_id"}, {"name": "amount"}],
                "foreign_keys": [],
            },
        ]
    }

    filtered = SchemaSelector.select(
        snapshot, "Show names of users", preferred_tables=[]
    )

    table_names = [t["name"] for t in filtered["tables"]]

    assert "users" in table_names
    assert "orders" not in table_names


def test_schema_selector_no_match_returns_tables():

    snapshot = {
        "tables": [
            {"name": "users", "columns": [], "foreign_keys": []},
            {"name": "orders", "columns": [], "foreign_keys": []},
        ]
    }

    filtered = SchemaSelector.select(snapshot, "random query", preferred_tables=[])

    assert len(filtered["tables"]) > 0


def test_schema_selector_empty_schema():

    filtered = SchemaSelector.select({}, "anything", preferred_tables=[])

    assert filtered == {"tables": []}
