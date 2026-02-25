from __future__ import annotations

import json
from pathlib import Path

from krako2.autoscaling.controller import AutoscalingController, Metrics
from krako2.domain.models import EventType


class DummyPublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def emit(self, event_type, *, idempotency_key: str, work_unit_id=None, payload=None):
        self.events.append(
            {
                "type": event_type.value if hasattr(event_type, "value") else str(event_type),
                "idempotency_key": idempotency_key,
                "payload": payload or {},
            }
        )
        return {"id": f"evt-{len(self.events)}"}, True


def test_scale_up_after_3_windows(tmp_path: Path) -> None:
    pub = DummyPublisher()
    ctrl = AutoscalingController(state_path=tmp_path / "capacity_state.json", publisher=pub)
    m = Metrics(queue_depth=300, w95_wait_s=2.5, utilization=0.85)

    ctrl.evaluate(m)
    ctrl.evaluate(m)
    out = ctrl.evaluate(m)

    assert out["capacity_state"]["R"] == 2
    assert any(e["type"] == EventType.CAPACITY_SCALE_REQUESTED.value for e in pub.events)


def test_scale_down_after_6_windows(tmp_path: Path) -> None:
    pub = DummyPublisher()
    state_path = tmp_path / "capacity_state.json"
    ctrl = AutoscalingController(state_path=state_path, publisher=pub)

    # Seed state above min replicas so scale-down can occur.
    state = ctrl.load_state()
    state["R"] = 3
    state["last_scale_down_ts"] = 0.0
    ctrl.save_state_atomic(state)

    m = Metrics(queue_depth=10, w95_wait_s=0.2, utilization=0.2)
    for _ in range(5):
        ctrl.evaluate(m)
    out = ctrl.evaluate(m)

    assert out["capacity_state"]["R"] == 2
    assert any(e["type"] == EventType.CAPACITY_SCALE_REQUESTED.value for e in pub.events)


def test_admission_mode_transitions_to_throttled_and_critical(tmp_path: Path) -> None:
    pub = DummyPublisher()
    ctrl = AutoscalingController(state_path=tmp_path / "capacity_state.json", publisher=pub)

    throttled = ctrl.evaluate(Metrics(queue_depth=900, w95_wait_s=2.1, utilization=0.82))
    assert throttled["capacity_state"]["mode"] == "THROTTLED"

    ctrl.evaluate(Metrics(queue_depth=1000, w95_wait_s=5.0, utilization=0.95))
    ctrl.evaluate(Metrics(queue_depth=1000, w95_wait_s=5.0, utilization=0.95))
    critical = ctrl.evaluate(Metrics(queue_depth=1000, w95_wait_s=5.0, utilization=0.95))

    assert critical["capacity_state"]["mode"] == "CRITICAL"
    assert any(e["type"] == EventType.CAPACITY_ADMISSION_MODE_CHANGED.value for e in pub.events)
