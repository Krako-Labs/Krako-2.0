from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class BreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class NodeBreaker:
    state: BreakerState = BreakerState.CLOSED
    attempts: deque[tuple[float, bool]] = field(default_factory=deque)  # (timestamp, success)
    timeout_timestamps: deque[float] = field(default_factory=deque)
    open_until_ts: float = 0.0
    half_open_probe_every_s: float = 5.0
    last_probe_ts: float = 0.0
    half_open_consecutive_successes: int = 0


class CircuitBreakerManager:
    def __init__(self, open_duration_s: float = 30.0) -> None:
        self.open_duration_s = open_duration_s
        self._nodes: dict[str, NodeBreaker] = {}

    def _node(self, node_id: str) -> NodeBreaker:
        if node_id not in self._nodes:
            self._nodes[node_id] = NodeBreaker()
        return self._nodes[node_id]

    def _prune(self, node: NodeBreaker, now: float) -> None:
        while node.attempts and now - node.attempts[0][0] > 60.0:
            node.attempts.popleft()
        while node.timeout_timestamps and now - node.timeout_timestamps[0] > 30.0:
            node.timeout_timestamps.popleft()

    def current_state(self, node_id: str, now: float | None = None) -> BreakerState:
        now = time.monotonic() if now is None else now
        node = self._node(node_id)

        if node.state == BreakerState.OPEN and now >= node.open_until_ts:
            node.state = BreakerState.HALF_OPEN
            node.half_open_consecutive_successes = 0

        return node.state

    def can_attempt(self, node_id: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        node = self._node(node_id)
        state = self.current_state(node_id, now)

        if state == BreakerState.CLOSED:
            return True
        if state == BreakerState.OPEN:
            return False

        if now - node.last_probe_ts >= node.half_open_probe_every_s:
            node.last_probe_ts = now
            return True
        return False

    def record_attempt(
        self,
        node_id: str,
        *,
        success: bool,
        timeout: bool = False,
        now: float | None = None,
    ) -> BreakerState:
        now = time.monotonic() if now is None else now
        node = self._node(node_id)
        self.current_state(node_id, now)

        node.attempts.append((now, success))
        if timeout:
            node.timeout_timestamps.append(now)
        self._prune(node, now)

        if node.state == BreakerState.HALF_OPEN:
            if success:
                node.half_open_consecutive_successes += 1
                if node.half_open_consecutive_successes >= 5:
                    node.state = BreakerState.CLOSED
                    node.half_open_consecutive_successes = 0
            else:
                node.state = BreakerState.OPEN
                node.open_until_ts = now + self.open_duration_s
                node.half_open_consecutive_successes = 0
            return node.state

        total_attempts = len(node.attempts)
        failures = sum(1 for _, ok in node.attempts if not ok)
        failure_rate = (failures / total_attempts) if total_attempts > 0 else 0.0
        timeout_burst = len(node.timeout_timestamps)

        if (total_attempts >= 60 and failure_rate > 0.5) or timeout_burst >= 20:
            node.state = BreakerState.OPEN
            node.open_until_ts = now + self.open_duration_s

        return node.state
