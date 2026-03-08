import re
from dataclasses import dataclass

from app.core.constants import DEFAULT_AUTOLIMIT, MAX_LIMIT_ALLOWED, DatabaseDialect
from app.core.exceptions import PolicyViolationError
from app.schemas.validation_schema import ValidationOutput

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


def _normalize_sql(sql: str) -> str:
    sql = _strip_comments(sql)
    sql = sql.strip().rstrip(";")
    sql = re.sub(_WHITESPACE_RE, " ", sql)

    return sql


@dataclass(frozen=True)
class PolicyEngine:
    dialect: DatabaseDialect = DatabaseDialect.POSTGRES
    auto_limit: int = DEFAULT_AUTOLIMIT
    max_limit: int = MAX_LIMIT_ALLOWED

    def enforce_readonly(self, sql: str) -> ValidationOutput:
        normalized = _normalize_sql(sql)

        if _FORBIDDEN_KEYWORDS.search(normalized):
            raise PolicyViolationError(
                "Error: DDL/DML statements are not allowed (read-only policy)!"
            )

        if not _SELECT_RE.match(normalized):
            raise PolicyViolationError("Error: Only SELECT queries are allowed!")

        contains_select_star = bool(
            re.search(r"\bSELECT\s+\*\b", normalized, re.IGNORECASE)
        )

        limit_injected = False
        limit_value = None

        m = _LIMIT_RE.search(normalized)

        if not m:
            normalized = f"{normalized} LIMIT {self.auto_limit}"
            limit_injected = True
            limit_value = self.auto_limit
        else:
            limit_value = int(m.group(1))
            if limit_value > self.max_limit:
                raise PolicyViolationError(
                    f"Error: LIMIT {limit_value} exceeds max allowed LIMIT {self.max_limit}!"
                )

        # Risk classification
        risk = "medium" if contains_select_star else "low"

        return ValidationOutput(
            ok=True,
            risk_level=risk,
            limit_injected=limit_injected,
            limit_value=limit_value,
            contains_select_star=contains_select_star,
            normalized_sql=normalized,
        )
