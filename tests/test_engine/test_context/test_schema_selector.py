from app.context.schema_selector import SchemaSelector


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

    filtered = SchemaSelector.select(snapshot, "Show names of users")

    table_names = [t["name"] for t in filtered["tables"]]

    assert "users" in table_names
    assert "orders" not in table_names
