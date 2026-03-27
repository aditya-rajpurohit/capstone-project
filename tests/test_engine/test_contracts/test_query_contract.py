from app.engine.contracts.query_contract import QueryOutput


def test_query_output():
    obj = QueryOutput(sql="SELECT 1", confidence=0.8)

    assert obj.sql == "SELECT 1"
    assert obj.confidence == 0.8
