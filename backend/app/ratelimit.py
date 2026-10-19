import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Tuple


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_s: float = 60.0, clock: Callable[[], float] = time.monotonic):
        self.max, self.window, self.clock = max_requests, window_s, clock
        self.hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> Tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        now, q = self.clock(), self.hits[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.max:
            return False, max(1, int(self.window - (now - q[0])) + 1)
        q.append(now)
        return True, 0
