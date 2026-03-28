from app.core.constants import DatabaseDialect, EngineState


def test_engine_state_enum():
    assert EngineState.INIT.value == "INIT"
    assert EngineState.PLAN.value == "PLAN"
    assert EngineState.QUERY_GENERATION.value == "QUERY_GENERATION"
    assert EngineState.VALIDATION.value == "VALIDATION"
    assert EngineState.EXECUTION.value == "EXECUTION"
    assert EngineState.REFLECTION.value == "REFLECTION"
    assert EngineState.DONE.value == "DONE"
    assert EngineState.FAILED.value == "FAILED"


def test_database_dialect_enum():
    assert DatabaseDialect.POSTGRES.value == "POSTGRES"
    assert DatabaseDialect.MYSQL.value == "MYSQL"
    assert DatabaseDialect.SQLITE.value == "SQLITE"
    assert DatabaseDialect.MSSQL.value == "MSSQL"
    assert DatabaseDialect.MONGODB.value == "MONGODB"
