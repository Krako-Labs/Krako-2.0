from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from krako2.domain.models import Event
from krako2.scheduler.node_registry import NodeRegistry


class TrustConsumer:
    def __init__(
        self,
        state_path: str | Path = "data/trust_state.json",
        registry_path: str | Path = "data/node_registry.json",
    ) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.node_registry = NodeRegistry(registry_path=registry_path)
        if not self.state_path.exists():
            self._write_state({"processed_event_ids": [], "work_units": {}, "nodes": {}})

    def _read_state(self) -> dict:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state: dict) -> None:
        tmp_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.state_path)

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(0.0, min(1.0, value))

    def consume(self, event: Event) -> bool:
        state = self._read_state()
        processed = set(state.get("processed_event_ids", []))
        if event.id in processed:
            return False

        if event.type.value == "node.health.updated":
            payload = event.payload or {}
            node_id = payload.get("node_id")
            if isinstance(node_id, str) and node_id:
                self.node_registry.apply_heartbeat(payload)
                nodes = state.setdefault("nodes", {})
                node_state = dict(nodes.get(node_id, {}))
                prev_score = float(node_state.get("score", 0.5))
                prev_ewma = float(node_state.get("ewma_health", 0.5))

                health_status = str(payload.get("health_status", "healthy"))
                if health_status == "healthy":
                    delta = 0.01
                    signal = 1.0
                elif health_status == "degraded":
                    delta = -0.05
                    signal = 0.5
                else:
                    delta = -0.2
                    signal = 0.0

                ewma = 0.2 * signal + 0.8 * prev_ewma
                score = self._clamp_score(prev_score + delta)
                last_seen_ts = str(payload.get("timestamp", datetime.now(timezone.utc).isoformat()))

                nodes[node_id] = {
                    "last_seen_ts": last_seen_ts,
                    "health_status": health_status,
                    "ewma_health": ewma,
                    "score": score,
                }
        else:
            work_units = state.setdefault("work_units", {})
            if event.work_unit_id:
                work_units[event.work_unit_id] = {
                    "last_event_id": event.id,
                    "last_event_type": event.type.value,
                    "trust_score": float(event.payload.get("trust_score", 1.0)),
                }

        processed.add(event.id)
        state["processed_event_ids"] = sorted(processed)
        self._write_state(state)
        return True
