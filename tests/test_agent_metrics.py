from __future__ import annotations

import json
from pathlib import Path

from krako2.agent.agent import NodeAgent


def _append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _scheduled_event(event_id: str = "evt-1") -> dict:
    return {
        "id": event_id,
        "type": "workunit.scheduled",
        "idempotency_key": f"schedule:wu:{event_id}",
        "work_unit_id": f"wu:{event_id}",
        "payload": {
            "selected_node_id": "node-1",
            "simulated_ms": 0,
            "tenant_id": "tenant-a",
            "correlation_id": "sess:test",
            "attempt_index": 1,
            "llm_tokens": 0,
        },
    }


def test_metrics_increase_then_decrease_on_processing(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _append_event(events, _scheduled_event("e1"))

    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "agent_state.json")
    out = agent.poll_once()
    assert out["processed"] == 1

    state = json.loads((tmp_path / "agent_state.json").read_text(encoding="utf-8"))
    assert state["active_queue_depth"] == 0

    rows = _read_events(events)
    heartbeats = [r for r in rows if r.get("type") == "node.health.updated"]
    assert len(heartbeats) >= 2


def test_heartbeat_payload_reflects_dynamic_metrics(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _append_event(events, _scheduled_event("e2"))

    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "agent_state.json")
    agent.poll_once()

    rows = _read_events(events)
    heartbeats = [r for r in rows if r.get("type") == "node.health.updated"]
    q_values = [hb.get("payload", {}).get("active_queue_depth") for hb in heartbeats]
    assert any(v == 1 for v in q_values)
    assert q_values[-1] == 0


def test_metrics_persist_across_restart(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _append_event(events, _scheduled_event("e3"))

    state_path = tmp_path / "agent_state.json"
    agent1 = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=state_path)
    agent1.poll_once()

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    agent2 = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=state_path)

    assert agent2.active_queue_depth == persisted["active_queue_depth"]
    assert agent2.utilization == persisted["utilization"]
    assert agent2.available_concurrency == persisted["available_concurrency"]
