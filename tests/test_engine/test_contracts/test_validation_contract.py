from app.engine.contracts.validation_contract import ValidationOutput


def test_validation_output():
    obj = ValidationOutput(ok=True, risk_level="low")

    assert obj.ok is True
    assert obj.limit_injected is False
