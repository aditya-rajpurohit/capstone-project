import re
from typing import Any, Optional


class SchemaSelector:
    """
    Layer 1 Schema Selector (Deterministic, No LLM)

    Goal:
    - Reduce schema prompt size by selecting only relevant tables/columns for a user query.
    - Deterministic + bounded output (no randomization, no heuristics that depend on runtime state).
    - Works on the stored schema snapshot format:
        {
          "tables": [
            {
              "name": str,
              "columns": [{"name": str, ...}, ...],
              "foreign_keys": [{"column": str, "ref_table": str, "ref_column": str}, ...]
            },
            ...
          ]
        }

    Selection rules (MVP):
    1) Tokenize user_query into normalized tokens.
    2) Score each table using:
       - table name token match (strong)
       - column token match (medium)
       - foreign key ref_table match (weak)
    3) Keep top N tables (bounded).
    4) For kept tables, keep:
       - matched columns (first)
       - important key columns (id, *_id, created_at, updated_at) (second)
       - then fill remaining up to max_cols_per_table
    5) Always include foreign_keys for kept tables (small + helps joins).
    """

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        text = text.lower()
        # words like users, user_id, order, amount, etc.
        toks = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text)
        return set(toks)

    DEFAULT_MAX_TABLES: int = 10
    DEFAULT_MAX_COLS_PER_TABLE: int = 12

    IMPORTANT_COLS: set[str] = {
        "id",
        "created_at",
        "updated_at",
    }

    IMPORTANT_SUFFIXES: tuple[str, ...] = ("_id",)

    @classmethod
    def _is_important_col(cls, col_name: str) -> bool:
        cn = col_name.lower()
        if cn in cls.IMPORTANT_COLS:
            return True
        return any(cn.endswith(suf) for suf in cls.IMPORTANT_SUFFIXES)

    @classmethod
    def select(
        cls,
        schema_snapshot: dict[str, Any],
        user_query: str,
        *,
        max_tables: int | None = None,
        max_cols_per_table: int | None = None,
        include_if_no_match: bool = True,
        preferred_tables: Optional[list[Any]] = None
    ) -> dict[str, Any]:
        """
        Returns a reduced schema snapshot in the same shape: {"tables":[...]}.

        include_if_no_match:
          - If True and no tables match, return first N tables (bounded) to avoid empty schema.
          - If False and no tables match, return {"tables": []}.
        """
        
        if not schema_snapshot or "tables" not in schema_snapshot:
            return {"tables": []}

        max_tables = max_tables or cls.DEFAULT_MAX_TABLES
        max_cols_per_table = max_cols_per_table or cls.DEFAULT_MAX_COLS_PER_TABLE

        tables: list[dict[str, Any]] = list(schema_snapshot.get("tables", []))
        tokens = cls._tokenize(user_query)

        scored: list[tuple[int, dict[str, Any]]] = []

        for t in tables:
            table_name = (t.get("name") or "").lower()
            cols = list(t.get("columns", []) or [])
            fks = list(t.get("foreign_keys", []) or [])

            score = 0

            # Table name match
            if table_name and table_name in tokens:
                score += 8
            else:
                # allow partial hits like "user" token matching "users"
                # purely deterministic string containment
                for token in tokens:
                    if token and (token in table_name or table_name in token):
                        score += 4
                        break

            # Column matches
            col_hits = 0
            for c in cols:
                cname = (c.get("name") or "").lower()
                if not cname:
                    continue
                if cname in tokens:
                    score += 3
                    col_hits += 1
                else:
                    for token in tokens:
                        if token and (token in cname or cname in token):
                            score += 1
                            col_hits += 1
                            break

            # FK hinting (weak)
            for fk in fks:
                ref_table = (fk.get("ref_table") or "").lower()
                if ref_table and ref_table in tokens:
                    score += 1

            scored.append((score, t))

        # sort by score desc, then by table name for stable ordering
        scored.sort(key=lambda x: (-x[0], (x[1].get("name") or "")))

        # pick tables with score>0 first
        matched = [t for s, t in scored if s > 0]
        if not matched:
            if not include_if_no_match:
                return {"tables": []}
            matched = [t for _, t in scored[:max_tables]]

        selected_tables = matched[:max_tables]

        # Now select columns per table deterministically
        reduced_tables: list[dict[str, Any]] = []
        for t in selected_tables:
            cols = list(t.get("columns", []) or [])
            fks = list(t.get("foreign_keys", []) or [])

            # matched columns first
            matched_cols: list[dict[str, Any]] = []
            important_cols: list[dict[str, Any]] = []
            other_cols: list[dict[str, Any]] = []

            for c in cols:
                cname = c.get("name") or ""
                cname_l = cname.lower()

                is_match = False
                if cname_l in tokens:
                    is_match = True
                else:
                    for token in tokens:
                        if token and (token in cname_l or cname_l in token):
                            is_match = True
                            break

                if is_match:
                    matched_cols.append(c)
                elif cname and cls._is_important_col(cname):
                    important_cols.append(c)
                else:
                    other_cols.append(c)

            # merge unique by column name while preserving order
            seen: set[str] = set()
            selected_cols: list[dict[str, Any]] = []

            def add_cols(bucket: list[dict[str, Any]]) -> None:
                nonlocal selected_cols
                for c in bucket:
                    name = c.get("name")
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    selected_cols.append(c)
                    if len(selected_cols) >= max_cols_per_table:
                        return

            add_cols(matched_cols)
            add_cols(important_cols)
            add_cols(other_cols)

            reduced_tables.append(
                {
                    "name": t.get("name"),
                    "columns": selected_cols,
                    "foreign_keys": fks,
                }
            )

        return {"tables": reduced_tables}
