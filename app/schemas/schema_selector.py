import re
from typing import Any


class SchemaSelector:
    """
    Deterministic MVP:
    - Tokenize user query
    - Keep tables/columns that match tokens
    - Always keep PK-ish columns and join keys if present
    - Hard cap on tables/columns to avoid schema flooding
    """

    DEFAULT_MAX_TABLES = 12
    DEFAULT_MAX_COLS_PER_TABLE = 12

    @staticmethod
    def _tokens(text: str) -> set[str]:
        text = text.lower()
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)

        return set(tokens)

    @classmethod
    def select(
        cls,
        schema_snapshot: dict[str, Any],
        user_query: str,
        max_tables: int | None = None,
        max_cols_per_table: int | None = None,
    ) -> dict[str, Any]:
        max_tables = max_tables or cls.DEFAULT_MAX_TABLES
        max_cols_per_table = max_cols_per_table or cls.DEFAULT_MAX_COLS_PER_TABLE

        tokens = cls._tokens(user_query)

        tables = schema_snapshot.get("tables", [])
        scored = []

        for t in tables:
            table_name = (t.get("name") or "").lower()
            cols = t.get("columns", [])
            fks = t.get("foreign_keys", [])

            score = 0
            if table_name in tokens:
                score += 5

            col_hits = []
            for c in cols:
                cname = (c.get("name") or "").lower()
                if cname in tokens:
                    score += 2
                    col_hits.append(c)

            # keep important columns even if not matched
            important = []
            for c in cols:
                cname = (c.get("name") or "").lower()
                if cname in {"id", "user_id", "account_id", "created_at", "updated_at"}:
                    important.append(c)

            # merge unique cols (hits first)
            seen = set()
            selected_cols = []
            for c in col_hits + important + cols:
                name = c.get("name")
                if not name or name in seen:
                    continue
                seen.add(name)
                selected_cols.append(c)
                if len(selected_cols) >= max_cols_per_table:
                    break

            # if nothing relevant and score low, skip table
            if score == 0 and not col_hits:
                continue

            scored.append(
                (
                    score,
                    {
                        "name": t.get("name"),
                        "columns": selected_cols,
                        "foreign_keys": fks,
                    },
                )
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        selected_tables = [t for _, t in scored[:max_tables]]

        return {"tables": selected_tables}
