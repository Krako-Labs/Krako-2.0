from __future__ import annotations

import json
from pathlib import Path

from krako2.domain.models import Event


class BillingConsumer:
    def __init__(self, ledger_path: str | Path = "data/billing_ledger.jsonl") -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.touch(exist_ok=True)

    def _processed_event_ids(self) -> set[str]:
        ids: set[str] = set()
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                ids.add(record["event_id"])
        return ids

    def consume(self, event: Event) -> bool:
        if event.id in self._processed_event_ids():
            return False

        record = {
            "event_id": event.id,
            "event_type": event.type.value,
            "work_unit_id": event.work_unit_id,
            "amount": float(event.payload.get("amount", 0.0)),
            "currency": event.payload.get("currency", "USD"),
        }
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
