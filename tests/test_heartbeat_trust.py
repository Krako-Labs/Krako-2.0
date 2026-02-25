from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from krako2.agent.agent import NodeAgent
from krako2.domain.models import WorkUnit
from krako2.scheduler.node_registry import Node
from krako2.scheduler.service import SchedulerService
from krako2.storage.event_log import EventLog
from krako2.trust.consumer import TrustConsumer


def test_agent_emits_heartbeat_event(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "agent_state.json")

    assert agent.emit_heartbeat() is True

    rows = [e.model_dump(mode="json") for e in EventLog(events).read_events()]
    assert len(rows) == 1
    assert rows[0]["type"] == "node.health.updated"
    assert rows[0]["payload"]["node_id"] == "node-1"


def test_trust_updates_on_heartbeat(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    agent = NodeAgent(node_id="node-1", data_dir=tmp_path, event_log_path=events, state_path=tmp_path / "agent_state.json")
    trust = TrustConsumer(state_path=tmp_path / "trust_state.json")

    agent.emit_heartbeat()
    event = EventLog(events).read_events()[0]
    assert trust.consume(event) is True

    state = json.loads((tmp_path / "trust_state.json").read_text(encoding="utf-8"))
    node = state["nodes"]["node-1"]
    assert node["health_status"] == "healthy"
    assert node["score"] >= 0.5
    assert 0.0 <= node["ewma_health"] <= 1.0


def test_scheduler_applies_freshness_penalty(tmp_path: Path) -> None:
    trust_path = tmp_path / "trust_state.json"
    stale_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    trust_path.write_text(
        json.dumps(
            {
                "processed_event_ids": [],
                "work_units": {},
                "nodes": {
                    "node-1": {
                        "last_seen_ts": stale_ts,
                        "health_status": "healthy",
                        "ewma_health": 1.0,
                        "score": 0.8,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    service = SchedulerService(
        state_path=tmp_path / "scheduler_state.json",
        retry_budget_state_path=tmp_path / "retry_budget_state.json",
        congestion_state_path=tmp_path / "congestion_state.json",
        trust_state_path=trust_path,
    )
    node = Node(
        node_id="node-1",
        enabled=True,
        health_status="healthy",
        supported_kinds=["cpu"],
        available_concurrency=4,
        active_queue_depth=0,
        utilization=0.2,
        trust_score=0.9,
        region="eu-west",
        version="0.1.0",
    )
    _, components = service._node_score(node, WorkUnit(kind="cpu", region="eu-west"))

    assert components["T"] == 0.4
