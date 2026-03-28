import re

FULL_SCAN_PATTERN = re.compile(r"\bSELECT\s+\*\b", re.IGNORECASE)
NO_WHERE_PATTERN = re.compile(r"\bSELECT\b.*\bFROM\b", re.IGNORECASE)


class QueryCostEstimator:
    """
    Basic query cost estimation.

    Prevents:
    - SELECT *
    - missing WHERE filters (heuristic)
    """

    @staticmethod
    def estimate(sql: str) -> str:

        if FULL_SCAN_PATTERN.search(sql):
            return "high"

        if NO_WHERE_PATTERN.search(sql) and "where" not in sql.lower():
            return "medium"

        return "low"
