import re
from dataclasses import dataclass

from app.core.constants import (DEFAULT_AUTOLIMIT, MAX_LIMIT_ALLOWED,
                                DatabaseDialect)
from app.core.exceptions import PolicyViolationError

_SQL_COMMENT_RE = re.compile(r"(--[^\n]*\n)|(/\*.*?\*/)", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|MERGE|CALL)\b",
    re.IGNORECASE,
)

_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    return re.sub(_SQL_COMMENT_RE, " ", sql)


def normalize_sql(sql: str) -> str:
    sql = _strip_comments(sql)
    sql = sql.strip().rstrip(";")
    sql = re.sub(_WHITESPACE_RE, " ", sql)

    return sql


@dataclass(frozen=True)
class SQLPolicyEngine:
    dialect: DatabaseDialect = DatabaseDialect.POSTGRES
    auto_limit: int = DEFAULT_AUTOLIMIT
    max_limit: int = MAX_LIMIT_ALLOWED

    def enforce_readonly(self, sql: str) -> str:
        normalized = normalize_sql(sql)

        if _FORBIDDEN_KEYWORDS.search(normalized):
            raise PolicyViolationError(
                "DDL/DML statements are not allowed (read-only policy)."
            )

        if not _SELECT_RE.match(normalized):
            raise PolicyViolationError(
                "Only SELECT queries are allowed in Iteration 1."
            )

        limited = self._inject_or_validate_limit(normalized)

        return limited

    def _inject_or_validate_limit(self, sql: str) -> str:
        m = _LIMIT_RE.search(sql)

        if not m:
            return f"{sql} LIMIT {self.auto_limit}"

        limit_val = int(m.group(1))
        if limit_val > self.max_limit:
            raise PolicyViolationError(
                f"LIMIT {limit_val} exceeds max allowed LIMIT {self.max_limit}."
            )

        return sql
