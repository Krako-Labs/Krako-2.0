from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from krako2.billing.consumer import BillingConsumer
from krako2.storage.event_log import EventLog
from krako2.trust.consumer import TrustConsumer


def _reset_outputs(data_dir: Path) -> None:
    (data_dir / "billing_ledger.jsonl").unlink(missing_ok=True)
    (data_dir / "trust_state.json").unlink(missing_ok=True)


def main() -> int:
    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    event_log = EventLog(data_dir / "events.jsonl")
    events = event_log.read_events()

    _reset_outputs(data_dir)
    billing = BillingConsumer(data_dir / "billing_ledger.jsonl")
    trust = TrustConsumer(data_dir / "trust_state.json")

    billing_count = 0
    trust_count = 0
    for event in events:
        if billing.consume(event):
            billing_count += 1
        if trust.consume(event):
            trust_count += 1

    summary = {
        "replayed_events": len(events),
        "billing_records_written": billing_count,
        "trust_updates_written": trust_count,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
