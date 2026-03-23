from app.engine.contracts.schema_context_contract import SchemaContext


def test_schema_context():
    ctx = SchemaContext(dialect="POSTGRES", tables=[])

    assert ctx.dialect == "POSTGRES"
    assert ctx.tables == []
