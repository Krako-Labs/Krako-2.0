from __future__ import annotations

import json
from pathlib import Path

from krako2.agent.agent import NodeAgent
from krako2.agent.claim_index import is_claimed, load_index, record_claim, rebuild_from_event_log


def _append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def test_record_and_is_claimed(tmp_path: Path) -> None:
    index_path = tmp_path / "claim_index.json"

    assert is_claimed(index_path, "wu-1", "dispatch-1") is False

    record_claim(
        index_path,
        work_unit_id="wu-1",
        dispatch_event_id="dispatch-1",
        node_id="node-1",
        claim_event_id="claim-evt-1",
        ts_iso="2026-01-01T00:00:00+00:00",
    )

    assert is_claimed(index_path, "wu-1", "dispatch-1") is True
    assert is_claimed(index_path, "wu-1", "dispatch-x") is False

    idx = load_index(index_path)
    assert idx["version"] == "0.1"
    assert "wu-1:dispatch-1" in idx["claims"]


def test_rebuild_from_event_log_keeps_first_claim(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    index_path = tmp_path / "claim_index.json"

    _append_event(
        events_path,
        {
            "id": "claim-1",
            "type": "workunit.claimed",
            "idempotency_key": "claim:wu-1:dispatch-1:node-a",
            "work_unit_id": "wu-1",
            "payload": {
                "work_unit_id": "wu-1",
                "dispatch_event_id": "dispatch-1",
                "selected_node_id": "node-1",
                "node_id": "node-a",
            },
            "created_at": "2026-01-01T00:00:01+00:00",
        },
    )
    _append_event(
        events_path,
        {
            "id": "claim-2",
            "type": "workunit.claimed",
            "idempotency_key": "claim:wu-1:dispatch-1:node-b",
            "work_unit_id": "wu-1",
            "payload": {
                "work_unit_id": "wu-1",
                "dispatch_event_id": "dispatch-1",
                "selected_node_id": "node-1",
                "node_id": "node-b",
            },
            "created_at": "2026-01-01T00:00:02+00:00",
        },
    )

    idx = rebuild_from_event_log(index_path, events_path)
    entry = idx["claims"]["wu-1:dispatch-1"]
    assert entry["node_id"] == "node-a"
    assert entry["claim_event_id"] == "claim-1"


def test_agent_uses_index_to_skip_without_scan(tmp_path: Path, monkeypatch) -> None:
    events_path = tmp_path / "events.jsonl"
    index_path = tmp_path / "claim_index.json"

    dispatch_event = {
        "id": "dispatch-1",
        "type": "workunit.scheduled",
        "idempotency_key": "schedule:wu-1:1",
        "work_unit_id": "wu-1",
        "payload": {
            "selected_node_id": "node-1",
            "simulated_ms": 0,
            "tenant_id": "tenant-a",
        },
    }
    _append_event(events_path, dispatch_event)

    record_claim(
        index_path,
        work_unit_id="wu-1",
        dispatch_event_id="dispatch-1",
        node_id="node-0",
        claim_event_id="claim-existing",
        ts_iso="2026-01-01T00:00:00+00:00",
    )

    agent = NodeAgent(
        node_id="node-1",
        data_dir=tmp_path,
        event_log_path=events_path,
        state_path=tmp_path / "agent_state.json",
        claim_index_path=index_path,
    )

    def _raise_if_scan(*_args, **_kwargs):
        raise AssertionError("scan should not be used when index is valid")

    monkeypatch.setattr(agent, "_is_claimed_via_scan", _raise_if_scan)

    out = agent.poll_once()
    assert out["processed"] == 0

    rows = _read_events(events_path)
    completed = [e for e in rows if e.get("type") == "workunit.completed" and e.get("work_unit_id") == "wu-1"]
    claimed = [
        e
        for e in rows
        if e.get("type") == "workunit.claimed"
        and (e.get("payload") or {}).get("dispatch_event_id") == "dispatch-1"
    ]
    assert len(completed) == 0
    # Existing external claim remains the only claim for this dispatch.
    assert len(claimed) == 0
