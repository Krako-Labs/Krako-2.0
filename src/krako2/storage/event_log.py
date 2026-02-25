from __future__ import annotations

import json
from pathlib import Path

from krako2.domain.models import Event


class EventLog:
    def __init__(self, path: str | Path = "data/events.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _read_lines(self) -> list[str]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def read_events(self) -> list[Event]:
        events: list[Event] = []
        for line in self._read_lines():
            events.append(Event.model_validate_json(line))
        return events

    def _seen_idempotency_keys(self) -> set[str]:
        keys: set[str] = set()
        for event in self.read_events():
            keys.add(event.idempotency_key)
        return keys

    def append(self, event: Event) -> bool:
        if event.idempotency_key in self._seen_idempotency_keys():
            return False

        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return True
