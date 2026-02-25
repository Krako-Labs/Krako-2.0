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


def test_agent_ignores_scheduled_for_other_node(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _append_event(
        events,
        {
            "id": "evt-1",
            "type": "workunit.scheduled",
            "idempotency_key": "schedule:wu-1:1",
            "work_unit_id": "wu-1",
            "payload": {"selected_node_id": "node-x", "simulated_ms": 0},
        },
    )

    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "state.json")
    result = agent.poll_once()

    assert result["processed"] == 0
    all_events = _read_events(events)
    assert len([e for e in all_events if e.get("type") == "workunit.completed"]) == 0


def test_agent_processes_once_and_emits_completed(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    _append_event(
        events,
        {
            "id": "evt-2",
            "type": "workunit.scheduled",
            "idempotency_key": "schedule:wu-2:1",
            "work_unit_id": "wu-2",
            "payload": {
                "selected_node_id": "node-1",
                "simulated_ms": 0,
                "tenant_id": "tenant-a",
                "llm_tokens": 12,
                "attempt_index": 1,
            },
        },
    )

    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "state.json")
    first = agent.poll_once()
    second = agent.poll_once()

    assert first["processed"] == 1
    assert second["processed"] == 0

    all_events = _read_events(events)
    completed = [e for e in all_events if e.get("type") == "workunit.completed"]
    assert len(completed) == 1
    assert completed[0]["payload"]["selected_node_id"] == "node-1"


def test_agent_resume_from_offset_does_not_reprocess(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    state_path = tmp_path / "state.json"

    _append_event(
        events,
        {
            "id": "evt-3",
            "type": "workunit.scheduled",
            "idempotency_key": "schedule:wu-3:1",
            "work_unit_id": "wu-3",
            "payload": {"selected_node_id": "node-1", "simulated_ms": 0},
        },
    )

    agent1 = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=state_path)
    assert agent1.poll_once()["processed"] == 1

    # New process/instance should resume from stored offset and not reprocess old dispatch.
    agent2 = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=state_path)
    assert agent2.poll_once()["processed"] == 0

    all_events = _read_events(events)
    completed = [e for e in all_events if e.get("type") == "workunit.completed"]
    assert len(completed) == 1
