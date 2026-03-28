class AgenticEngineError(Exception):
    """Base error for the NL→SQL engine"""


class ContractValidationError(AgenticEngineError):
    """Raised when an agent/tool output fails schema validation"""


class InvalidStateTransitionError(AgenticEngineError):
    """Raised when state machine transition is invalid"""


class PolicyViolationError(AgenticEngineError):
    """Raised when SQL violates enforced safety policy"""


class DataSourceExecutionError(AgenticEngineError):
    """Raised for DB execution failures (later used in Phase 2)"""
