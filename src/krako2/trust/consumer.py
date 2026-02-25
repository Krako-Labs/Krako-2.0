from __future__ import annotations

import json
from pathlib import Path

from krako2.domain.models import Event


class TrustConsumer:
    def __init__(self, state_path: str | Path = "data/trust_state.json") -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._write_state({"processed_event_ids": [], "work_units": {}})

    def _read_state(self) -> dict:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state: dict) -> None:
        with self.state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)

    def consume(self, event: Event) -> bool:
        state = self._read_state()
        processed = set(state.get("processed_event_ids", []))
        if event.id in processed:
            return False

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
