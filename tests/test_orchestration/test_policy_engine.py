import pytest

from app.core.exceptions import PolicyViolationError
from app.orchestration.policy_engine import SQLPolicyEngine


def test_reject_non_select():
    pe = SQLPolicyEngine()

    with pytest.raises(PolicyViolationError):
        pe.enforce_readonly("UPDATE users SET x=1;")


def test_injects_limit_when_missing():
    pe = SQLPolicyEngine(auto_limit=100)
    out = pe.enforce_readonly("SELECT id FROM users")

    assert out.upper().endswith("LIMIT 100")


def test_allows_limit_under_max():
    pe = SQLPolicyEngine(max_limit=1000)
    out = pe.enforce_readonly("SELECT id FROM users LIMIT 999")

    assert "LIMIT 999" in out.upper()


def test_rejects_limit_over_max():
    pe = SQLPolicyEngine(max_limit=1000)

    with pytest.raises(PolicyViolationError):
        pe.enforce_readonly("SELECT id FROM users LIMIT 5000")
