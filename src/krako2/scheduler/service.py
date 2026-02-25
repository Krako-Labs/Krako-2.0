from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SchedulerService:
    name: str = "krako2-scheduler"

    def tick(self) -> str:
        # Stub hook for future dispatch logic.
        return "ok"
