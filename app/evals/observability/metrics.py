import time


class LatencyTracker:

    def __init__(self):
        self.start = time.perf_counter()

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.start) * 1000)
