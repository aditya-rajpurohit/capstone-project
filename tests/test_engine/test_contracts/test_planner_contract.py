from app.engine.contracts.planner_contract import PlannerOutput


def test_planner_output():
    obj = PlannerOutput(intent="get_users", confidence=0.9)

    assert obj.intent == "get_users"
    assert obj.operation == "SELECT"
    assert obj.entities == []
    assert obj.constraints == []
