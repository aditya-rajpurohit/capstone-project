from app.engine.contracts.critic_contract import CriticOutput


def test_critic_output():
    obj = CriticOutput(logical_issues_detected=False, risk_level="low", confidence=0.95)

    assert obj.risk_level == "low"
