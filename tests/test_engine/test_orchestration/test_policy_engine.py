import pytest

from app.core.exceptions import PolicyViolationError
from app.evals.guardrails.policy_engine import SqlPolicyEngine


def test_reject_non_select():
    policy_engine = SqlPolicyEngine()

    with pytest.raises(PolicyViolationError):
        policy_engine.enforce_readonly("UPDATE users SET x=1;")


def test_injects_limit_when_missing():
    policy_engine = SqlPolicyEngine(auto_limit=100)

    validation = policy_engine.enforce_readonly("SELECT id FROM users")

    assert validation.ok is True
    assert validation.limit_injected is True
    assert validation.normalized_sql is not None
    assert validation.normalized_sql.upper().endswith("LIMIT 100")


def test_allows_limit_under_max():
    policy_engine = SqlPolicyEngine(max_limit=1000)

    validation = policy_engine.enforce_readonly("SELECT id FROM users LIMIT 999")

    assert validation.ok is True
    assert validation.limit_injected is False
    assert validation.normalized_sql is not None
    assert "LIMIT 999" in validation.normalized_sql.upper()


def test_rejects_limit_over_max():
    policy_engine = SqlPolicyEngine(max_limit=1000)

    with pytest.raises(PolicyViolationError):
        policy_engine.enforce_readonly("SELECT id FROM users LIMIT 5000")


def test_policy_engine_blocks_insert():
    policy_engine = SqlPolicyEngine()

    with pytest.raises(PolicyViolationError):
        policy_engine.enforce_readonly("INSERT INTO users VALUES (1)")
