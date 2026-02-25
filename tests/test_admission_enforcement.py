from __future__ import annotations

import json
from pathlib import Path

from krako2.domain.models import WorkUnit
from krako2.scheduler.node_registry import Node
from krako2.scheduler.service import SchedulerService
from krako2.storage.event_log import EventLog
from krako2.telemetry.publisher import EventPublisher


def _setup(tmp_path: Path, mode: str) -> tuple[SchedulerService, EventPublisher, list[Node]]:
    (tmp_path / "capacity_state.json").write_text(
        json.dumps({"mode": mode, "R": 1, "K": 4}, sort_keys=True),
        encoding="utf-8",
    )
    event_log = EventLog(tmp_path / "events.jsonl")
    publisher = EventPublisher(event_log)
    service = SchedulerService(
        state_path=tmp_path / "scheduler_state.json",
        retry_budget_state_path=tmp_path / "retry_budget_state.json",
        congestion_state_path=tmp_path / "congestion_state.json",
        trust_state_path=tmp_path / "trust_state.json",
        capacity_state_path=tmp_path / "capacity_state.json",
    )
    nodes = [
        Node(
            node_id="node-1",
            enabled=True,
            health_status="healthy",
            supported_kinds=["cpu", "llm_pod"],
            available_concurrency=4,
            active_queue_depth=0,
            utilization=0.2,
            trust_score=0.8,
            region="eu-west",
            version="0.1.0",
        )
    ]
    return service, publisher, nodes


def test_open_allows_p2_scheduling(tmp_path: Path) -> None:
    service, publisher, nodes = _setup(tmp_path, "OPEN")
    wu = WorkUnit(kind="cpu", region="eu-west", payload={"priority": "p2"})

    selected, debug = service.schedule_and_emit(wu, nodes, publisher)

    assert selected == "node-1"
    assert debug.get("reason_code") == "best_score"


def test_throttled_defers_p2(tmp_path: Path) -> None:
    service, publisher, nodes = _setup(tmp_path, "THROTTLED")
    wu = WorkUnit(kind="cpu", region="eu-west", payload={"priority": "p2"})

    selected, debug = service.schedule_and_emit(wu, nodes, publisher)

    assert selected is None
    assert debug.get("reason_code") == "admission_throttled"
    events = EventLog(tmp_path / "events.jsonl").read_events()
    assert any(e.type.value == "workunit.scheduling.deferred" for e in events)


def test_critical_rejects_p2_but_allows_p1(tmp_path: Path) -> None:
    service, publisher, nodes = _setup(tmp_path, "CRITICAL")

    p2 = WorkUnit(kind="cpu", region="eu-west", payload={"priority": "p2"})
    selected_p2, debug_p2 = service.schedule_and_emit(p2, nodes, publisher)
    assert selected_p2 is None
    assert debug_p2.get("reason_code") == "admission_rejected"

    p1 = WorkUnit(kind="cpu", region="eu-west", payload={"priority": "p1"})
    selected_p1, debug_p1 = service.schedule_and_emit(p1, nodes, publisher)
    assert selected_p1 == "node-1"
    assert debug_p1.get("reason_code") == "best_score"
