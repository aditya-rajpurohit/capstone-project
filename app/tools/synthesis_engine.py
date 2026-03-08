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

        successful_db_ids: list[str] = []
        failed_db_ids: list[str] = []

        successful_results: list[dict[str, Any]] = []

        for database_id, ctx in per_db_results.items():
            result = ctx.get("execution_result", {})

            if result.get("status") == "success":
                successful_db_ids.append(database_id)
                successful_results.append(result)
            else:
                failed_db_ids.append(database_id)

        # -------------------------------
        # Case 1: All Failed
        # -------------------------------
        if not successful_results:
            return {
                "status": "failed",
                "error": "All data sources failed.",
                "successful_db_ids": [],
                "failed_db_ids": failed_db_ids,
                "rows": [],
                "row_count": 0,
            }

        # -------------------------------
        # Case 2: Single Success
        # -------------------------------
        if len(successful_results) == 1:
            result = successful_results[0]

            return {
                "status": "success",
                "rows": result.get("rows", []),
                "row_count": result.get("row_count", 0),
                "successful_db_ids": successful_db_ids,
                "failed_db_ids": failed_db_ids,
            }

        # -------------------------------
        # Case 3: Multiple Success
        # Strict schema compatibility check
        # -------------------------------

        # Determine baseline schema (from first result)
        baseline_rows = successful_results[0].get("rows", [])

        # If no rows, allow union safely
        if not baseline_rows:
            merged_rows = []
            for r in successful_results:
                merged_rows.extend(r.get("rows", []))

            return {
                "status": "success",
                "rows": merged_rows,
                "row_count": len(merged_rows),
                "successful_db_ids": successful_db_ids,
                "failed_db_ids": failed_db_ids,
            }

        baseline_columns = set(baseline_rows[0].keys())

        for result in successful_results[1:]:
            rows = result.get("rows", [])

            if not rows:
                continue

            current_columns = set(rows[0].keys())

            if current_columns != baseline_columns:
                return {
                    "status": "failed",
                    "error": "Schema mismatch across data sources during synthesis.",
                    "successful_db_ids": successful_db_ids,
                    "failed_db_ids": failed_db_ids,
                    "rows": [],
                    "row_count": 0,
                }

        # All schemas match → safe UNION
        merged_rows = []
        for result in successful_results:
            merged_rows.extend(result.get("rows", []))

        return {
            "status": "success",
            "rows": merged_rows,
            "row_count": len(merged_rows),
            "successful_db_ids": successful_db_ids,
            "failed_db_ids": failed_db_ids,
        }
