from __future__ import annotations

import argparse

import uvicorn
from fastapi import FastAPI

from krako2.domain.models import EventType, WorkUnit
from krako2.storage.event_log import EventLog
from krako2.telemetry.publisher import EventPublisher

app = FastAPI(title="Krako 2.0 API")
_event_log = EventLog()
_publisher = EventPublisher(_event_log)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/work-units")
def submit_work_unit(work_unit: WorkUnit) -> dict[str, object]:
    event, created = _publisher.emit(
        EventType.WORKUNIT_SUBMITTED,
        idempotency_key=f"workunit:{work_unit.id}",
        work_unit_id=work_unit.id,
        payload={"kind": work_unit.kind, **work_unit.payload},
    )
    return {
        "work_unit_id": work_unit.id,
        "event_id": event.id,
        "event_created": created,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Krako 2.0 API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--check", action="store_true", help="Validate app import and exit")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.check:
        print("krako2.api.main import OK")
    else:
        uvicorn.run("krako2.api.main:app", host=args.host, port=args.port)
