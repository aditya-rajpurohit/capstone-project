
class SynthesisEngine:
    """
    Deterministic multi-DB merge engine.
    MVP supports:
      - Single DB passthrough
      - UNION (row concatenation)
    """

    @staticmethod
    def synthesize(per_db_results: dict[str, dict]) -> dict:

        # Filter successful DBs
        successful = [
            r for r in per_db_results.values()
            if r.get("execution_result", {}).get("status") == "success"
        ]

        if not successful:
            return {
                "status": "failed",
                "error": "All databases failed",
                "rows": [],
            }

        if len(successful) == 1:
            return successful[0]["execution_result"]

        # UNION merge
        merged_rows = []
        for r in successful:
            merged_rows.extend(r["execution_result"]["rows"])

        return {
            "status": "success",
            "rows": merged_rows,
            "row_count": len(merged_rows),
        }
