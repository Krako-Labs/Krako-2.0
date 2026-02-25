from __future__ import annotations

from pathlib import Path

from krako2.scheduler.circuit_breaker import BreakerState, CircuitBreakerManager
from krako2.scheduler.retry import compute_backoff_seconds
from krako2.scheduler.retry_budget import RetryBudgetStore


def test_backoff_deterministic_same_inputs() -> None:
    a = compute_backoff_seconds("wu-1", 3)
    b = compute_backoff_seconds("wu-1", 3)
    assert a == b


def test_backoff_caps_at_30s() -> None:
    delay = compute_backoff_seconds("wu-big", 20)
    assert delay <= 30.0
    assert delay == 30.0


def test_budget_blocks_when_empty(tmp_path: Path) -> None:
    budget = RetryBudgetStore(
        state_path=tmp_path / "retry_budget_state.json",
        capacity=2,
        refill_tokens_per_min=0,
    )

    assert budget.allow_retry("tenant-a") is True
    assert budget.allow_retry("tenant-a") is True
    assert budget.allow_retry("tenant-a") is False


def test_circuit_breaker_opens_and_half_open_probes() -> None:
    cb = CircuitBreakerManager(open_duration_s=10)

    now = 1000.0
    # 60 attempts with failure rate > 0.5
    for i in range(31):
        cb.record_attempt("node-1", success=False, now=now + i * 0.1)
    for i in range(29):
        cb.record_attempt("node-1", success=True, now=now + (31 + i) * 0.1)

    assert cb.current_state("node-1", now=1010.0) == BreakerState.OPEN
    assert cb.can_attempt("node-1", now=1010.0) is False

    # After open window expires, breaker moves to HALF_OPEN and allows one probe.
    assert cb.current_state("node-1", now=1021.0) == BreakerState.HALF_OPEN
    assert cb.can_attempt("node-1", now=1021.0) is True
    assert cb.can_attempt("node-1", now=1022.0) is False
    assert cb.can_attempt("node-1", now=1026.1) is True
