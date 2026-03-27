import time
from collections import defaultdict


class RateLimiter:
    """
    Simple in-memory rate limiter.
    """

    def __init__(self, limit: int = 30, window_seconds: int = 60):
        self.limit = limit
        self.window = window_seconds
        self.requests = defaultdict(list)

    def allow(self, key: str) -> bool:

        now = time.time()

        timestamps = self.requests[key]

        # remove old timestamps
        self.requests[key] = [t for t in timestamps if now - t < self.window]

        if len(self.requests[key]) >= self.limit:
            return False

        self.requests[key].append(now)
        return True
