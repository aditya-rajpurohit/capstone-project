import re

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard the above",
    r"reveal system prompt",
    r"show hidden instructions",
    r"override safety",
]


class PromptInjectionDetector:
    """
    Simple deterministic injection detector.
    Designed for MVP safety.
    """

    @staticmethod
    def detect(query: str) -> bool:
        q = query.lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, q):
                return True

        return False
