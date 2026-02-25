from __future__ import annotations

import json
import os
from pathlib import Path


class BillingLedgerWriter:
    def __init__(self, ledger_path: str | Path = "data/billing_ledger.jsonl") -> None:
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.touch(exist_ok=True)

    def append(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False, sort_keys=True)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            # Best-effort durability for append-only ledger.
            os.fsync(f.fileno())


class BillingDedupeStore:
    def __init__(self, dedupe_path: str | Path = "data/billing_dedupe.json") -> None:
        self.dedupe_path = Path(dedupe_path)
        self.dedupe_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.dedupe_path.exists():
            self._atomic_write({"processed_event_ids": []})

    def _read(self) -> dict:
        with self.dedupe_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _atomic_write(self, data: dict) -> None:
        tmp_path = self.dedupe_path.with_suffix(self.dedupe_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.dedupe_path)

    def has(self, event_id: str) -> bool:
        data = self._read()
        return event_id in set(data.get("processed_event_ids", []))

    def mark_processed(self, event_id: str) -> None:
        data = self._read()
        processed = set(data.get("processed_event_ids", []))
        if event_id in processed:
            return
        processed.add(event_id)
        data["processed_event_ids"] = sorted(processed)
        self._atomic_write(data)
