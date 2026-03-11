import re
from dataclasses import dataclass
from app.core.constants import (DEFAULT_AUTOLIMIT, MAX_LIMIT_ALLOWED, DatabaseDialect)
from app.core.exceptions import PolicyViolationError
from app.engine.contracts.validation_contract import ValidationOutput


_WHITESPACE_RE = re.compile(r"\s+")
_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_LIMIT_RE = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
_SELECT_STAR_RE = re.compile(r"\bSELECT\s+\*\b", re.IGNORECASE)
_SQL_COMMENT_RE = re.compile(r"(--[^\n]*\n)|(/\*.*?\*/)", re.DOTALL)
_FORBIDDEN_KEYWORDS = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|MERGE|CALL)\b", re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    return re.sub(_SQL_COMMENT_RE, " ", sql)


def _normalize_sql(sql: str) -> str:
    sql = _strip_comments(sql)
    sql = sql.strip().rstrip(";")
    sql = re.sub(_WHITESPACE_RE, " ", sql)
    return sql

@dataclass(frozen=True)
class SqlPolicyEngine:
    dialect: DatabaseDialect = DatabaseDialect.POSTGRES
    auto_limit: int = DEFAULT_AUTOLIMIT
    max_limit: int = MAX_LIMIT_ALLOWED

    def enforce_readonly(self, sql: str) -> ValidationOutput:
        normalized = _normalize_sql(sql)

        if _FORBIDDEN_KEYWORDS.search(normalized):
            raise PolicyViolationError("ERROR: DDL/DML statements are not allowed.")

        if not _SELECT_RE.match(normalized):
            raise PolicyViolationError("ERROR: Only SELECT queries are allowed.")

        contains_select_star = bool(_SELECT_STAR_RE.search(normalized))

        limit_match = _LIMIT_RE.search(normalized)

        if not limit_match:
            normalized = f"{normalized} LIMIT {self.auto_limit}"
            limit_value = self.auto_limit
            limit_injected = True
        else:
            limit_value = int(limit_match.group(1))
            limit_injected = False
            if limit_value > self.max_limit:
                raise PolicyViolationError(
                    f"LIMIT {limit_value} exceeds max allowed {self.max_limit}."
                )

        risk = "medium" if contains_select_star else "low"

        return ValidationOutput(
            ok=True,
            risk_level=risk,
            limit_injected=limit_injected,
            limit_value=limit_value,
            contains_select_star=contains_select_star,
            normalized_sql=normalized,
        )
