from __future__ import annotations

from krako2.domain.models import Event, EventType
from krako2.storage.event_log import EventLog


class EventPublisher:
    def __init__(self, event_log: EventLog) -> None:
        self.event_log = event_log

    def emit(
        self,
        event_type: EventType,
        *,
        idempotency_key: str,
        work_unit_id: str | None = None,
        payload: dict | None = None,
    ) -> tuple[Event, bool]:
        event = Event(
            type=event_type,
            idempotency_key=idempotency_key,
            work_unit_id=work_unit_id,
            payload=payload or {},
        )
        created = self.event_log.append(event)
        return event, created
