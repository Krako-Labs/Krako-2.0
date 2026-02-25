from __future__ import annotations

import json
from pathlib import Path

from krako2.agent.agent import NodeAgent
from krako2.billing.consumer import BillingConsumer
from krako2.storage.event_log import EventLog


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_execution_session_id_propagates_agent_to_billing(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"

    _append_jsonl(
        events_path,
        {
            "id": "dispatch-1",
            "type": "workunit.scheduled",
            "idempotency_key": "schedule:wu-1:1",
            "work_unit_id": "wu-1",
            "payload": {
                "selected_node_id": "node-1",
                "execution_session_id": "sess-123",
                "tenant_id": "tenant-a",
                "correlation_id": "sess:sess-123",
                "simulated_ms": 0,
                "llm_tokens": 0,
                "attempt_index": 1,
            },
        },
    )

    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events_path, state_path=tmp_path / "agent_state.json")
    result = agent.poll_once()
    assert result["processed"] == 1

    event_rows = _read_jsonl(events_path)
    completed = [r for r in event_rows if r.get("type") == "workunit.completed"]
    assert len(completed) == 1
    assert completed[0]["payload"].get("execution_session_id") == "sess-123"

    consumer = BillingConsumer(tmp_path / "billing_ledger.jsonl", tmp_path / "billing_dedupe.json")
    for event in EventLog(events_path).read_events():
        if event.type.value == "workunit.completed":
            consumer.consume(event)

    ledger_rows = _read_jsonl(tmp_path / "billing_ledger.jsonl")
    assert len(ledger_rows) == 1
    assert ledger_rows[0]["execution_session_id"] == "sess-123"
