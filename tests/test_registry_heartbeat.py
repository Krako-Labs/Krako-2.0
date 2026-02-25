from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from krako2.domain.models import Event, EventType, WorkUnit
from krako2.scheduler.node_registry import NodeRegistry
from krako2.scheduler.service import SchedulerService
from krako2.trust.consumer import TrustConsumer


def _heartbeat_event(node_id: str, *, q: int = 0, util: float = 0.2, cap: int = 4, region: str | None = None) -> Event:
    return Event(
        type=EventType.NODE_HEALTH_UPDATED,
        idempotency_key=f"hb:{node_id}",
        payload={
            "node_id": node_id,
            "health_status": "healthy",
            "active_queue_depth": q,
            "utilization": util,
            "available_concurrency": cap,
            "region": region,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def test_trust_consumer_updates_node_registry_on_heartbeat(tmp_path: Path) -> None:
    registry_path = tmp_path / "node_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "node-1",
                        "enabled": True,
                        "health_status": "degraded",
                        "supported_kinds": ["cpu"],
                        "available_concurrency": 1,
                        "active_queue_depth": 9,
                        "utilization": 0.9,
                        "trust_score": 0.5,
                        "region": "eu-west",
                        "version": "0.1.0",
                        "last_heartbeat_ts": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    trust = TrustConsumer(state_path=tmp_path / "trust_state.json", registry_path=registry_path)
    trust.consume(_heartbeat_event("node-1", q=2, util=0.3, cap=6, region="eu-west"))

    node = NodeRegistry(registry_path=registry_path).list_nodes()[0]
    assert node.node_id == "node-1"
    assert node.active_queue_depth == 2
    assert node.utilization == 0.3
    assert node.available_concurrency == 6


def test_node_registry_creates_node_on_unknown_heartbeat(tmp_path: Path) -> None:
    registry_path = tmp_path / "node_registry.json"
    trust = TrustConsumer(state_path=tmp_path / "trust_state.json", registry_path=registry_path)

    trust.consume(_heartbeat_event("node-new", q=1, util=0.2, cap=4, region="us-east"))

    nodes = NodeRegistry(registry_path=registry_path).list_nodes()
    created = next(n for n in nodes if n.node_id == "node-new")
    assert created.enabled is True
    assert created.supported_kinds == ["cpu"]
    assert created.region == "us-east"


def test_scheduler_uses_updated_registry_metrics_in_debug(tmp_path: Path) -> None:
    registry_path = tmp_path / "node_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "node_id": "node-1",
                        "enabled": True,
                        "health_status": "healthy",
                        "supported_kinds": ["cpu"],
                        "available_concurrency": 4,
                        "active_queue_depth": 0,
                        "utilization": 0.2,
                        "trust_score": 0.6,
                        "region": "eu-west",
                        "version": "0.1.0",
                        "last_heartbeat_ts": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "node_id": "node-2",
                        "enabled": True,
                        "health_status": "healthy",
                        "supported_kinds": ["cpu"],
                        "available_concurrency": 4,
                        "active_queue_depth": 0,
                        "utilization": 0.2,
                        "trust_score": 0.6,
                        "region": "eu-west",
                        "version": "0.1.0",
                        "last_heartbeat_ts": datetime.now(timezone.utc).isoformat(),
                    },
                ]
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    trust = TrustConsumer(state_path=tmp_path / "trust_state.json", registry_path=registry_path)
    trust.consume(_heartbeat_event("node-1", q=7, util=0.9, cap=4, region="eu-west"))

    nodes = NodeRegistry(registry_path=registry_path).list_nodes()
    scheduler = SchedulerService(
        state_path=tmp_path / "scheduler_state.json",
        retry_budget_state_path=tmp_path / "retry_budget_state.json",
        congestion_state_path=tmp_path / "congestion_state.json",
        trust_state_path=tmp_path / "trust_state.json",
        capacity_state_path=tmp_path / "capacity_state.json",
    )

    _, debug = scheduler.select_node_for_workunit(WorkUnit(kind="cpu", region="eu-west"), nodes)
    node1 = next(c for c in debug["ranked_candidates"] if c["node_id"] == "node-1")
    assert node1["active_queue_depth"] == 7
