from typing import Any


class SynthesisEngine:
    """
    Layer 1 Deterministic Multi-DB Synthesis Engine.

    Rules:
    1. If all DBs fail → overall FAILED
    2. If exactly one DB succeeds → passthrough
    3. If multiple DBs succeed:
         - Column sets must match exactly
         - Otherwise → FAILED (schema mismatch)
    """

    @staticmethod
    def synthesize(per_db_results: dict[str, dict[str, Any]]) -> dict[str, Any]:

        successful: list[str] = []
        failed: list[str] = []
        success_results: list[dict[str, Any]] = []

        for database_id, context in per_db_results.items():
            result = context.get("execution_result", {})

            if result.get("status") == "success":
                successful.append(database_id)
                success_results.append(result)
            else:
                failed.append(database_id)

        # -------------------------------
        # Case 1: All Failed
        # -------------------------------
        if not success_results:
            return {
                "status": "failed",
                "error": "All data sources failed.",
                "successful_db_ids": [],
                "failed_db_ids": failed,
                "rows": [],
                "row_count": 0,
            }

        # -------------------------------
        # Case 2: Single Success
        # -------------------------------
        if len(success_results) == 1:
            r = success_results[0]

            return {
                "status": "success",
                "rows": r.get("rows", []),
                "row_count": r.get("row_count", 0),
                "successful_db_ids": successful,
                "failed_db_ids": failed,
            }

        # -------------------------------
        # Case 3: Multiple Success
        # Strict schema compatibility check
        # -------------------------------

        # Determine baseline schema (from first result)
        baseline_rows = success_results[0].get("rows", [])

        # If no rows, allow union safely
        if not baseline_rows:
            merged = []
            for r in success_results:
                merged.extend(r.get("rows", []))

            return {
                "status": "success",
                "rows": merged,
                "row_count": len(merged),
                "successful_db_ids": successful,
                "failed_db_ids": failed,
            }

        baseline_columns = tuple(sorted(baseline_rows[0].keys()))

        for r in success_results[1:]:
            rows = r.get("rows", [])

            if not rows:
                continue

            current_columns = tuple(sorted(rows[0].keys()))

            if current_columns != baseline_columns:
                return {
                    "status": "failed",
                    "error": "Schema mismatch across data sources during synthesis.",
                    "successful_db_ids": successful,
                    "failed_db_ids": failed,
                    "rows": [],
                    "row_count": 0,
                }

        # All schemas match → safe UNION
        merged = []
        for r in success_results:
            merged.extend(r.get("rows", []))

        return {
            "status": "success",
            "rows": merged,
            "row_count": len(merged),
            "successful_db_ids": successful,
            "failed_db_ids": failed,
        }
