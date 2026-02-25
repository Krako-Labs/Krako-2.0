from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from krako2.domain.models import EventType
from krako2.telemetry.publisher import EventPublisher


@dataclass
class CapacityState:
    mode: str
    R: int
    K: int
    updated_at: float


@dataclass
class Metrics:
    queue_depth: int
    w95_wait_s: float
    utilization: float


class AutoscalingController:
    def __init__(self, state_path: Path, publisher: EventPublisher | None = None) -> None:
        self.state_path = Path(state_path)
        self.publisher = publisher
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self.save_state_atomic(
                {
                    "mode": "OPEN",
                    "R": 1,
                    "K": 4,
                    "updated_at": time.time(),
                    "last_scale_up_ts": 0.0,
                    "last_scale_down_ts": 0.0,
                    "up_count": 0,
                    "down_count": 0,
                    "critical_count": 0,
                    "open_recover_count": 0,
                }
            )

    def load_state(self) -> dict[str, Any]:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_state_atomic(self, state: dict[str, Any]) -> None:
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_path)

    def _emit(self, event_type: EventType, idempotency_key: str, payload: dict[str, Any]) -> None:
        if self.publisher is None:
            return
        self.publisher.emit(event_type, idempotency_key=idempotency_key, payload=payload)

    def evaluate(self, metrics: Metrics) -> dict[str, Any]:
        state = self.load_state()
        now = time.time()
        events_emitted = 0

        up_trigger = (
            metrics.queue_depth > 200
            or metrics.w95_wait_s > 2.0
            or metrics.utilization > 0.80
        )
        down_trigger = (
            metrics.queue_depth < 40
            and metrics.w95_wait_s < 1.0
            and metrics.utilization < 0.45
        )

        state["up_count"] = int(state.get("up_count", 0)) + (1 if up_trigger else 0)
        state["down_count"] = int(state.get("down_count", 0)) + (1 if down_trigger else 0)
        if not up_trigger:
            state["up_count"] = 0
        if not down_trigger:
            state["down_count"] = 0

        prev_mode = state.get("mode", "OPEN")
        mode = prev_mode
        if metrics.queue_depth >= 1000:
            state["critical_count"] = int(state.get("critical_count", 0)) + 1
        else:
            state["critical_count"] = 0

        if metrics.queue_depth >= 900:
            mode = "THROTTLED"
        if int(state.get("critical_count", 0)) >= 3:
            mode = "CRITICAL"

        if metrics.queue_depth < 500:
            state["open_recover_count"] = int(state.get("open_recover_count", 0)) + 1
        else:
            state["open_recover_count"] = 0

        if int(state.get("open_recover_count", 0)) >= 6:
            mode = "OPEN"

        if mode != prev_mode:
            state["mode"] = mode
            payload = {
                "previous_mode": prev_mode,
                "mode": mode,
                "metrics": asdict(metrics),
            }
            self._emit(
                EventType.CAPACITY_ADMISSION_MODE_CHANGED,
                idempotency_key=f"capacity:mode:{mode}:{int(now*1000)}",
                payload=payload,
            )
            events_emitted += 1

        prev_r = int(state.get("R", 1))
        new_r = prev_r

        if int(state.get("up_count", 0)) >= 3 and now - float(state.get("last_scale_up_ts", 0.0)) >= 60.0:
            new_r = min(20, prev_r + 1)
            state["up_count"] = 0
            if new_r != prev_r:
                state["last_scale_up_ts"] = now

        if int(state.get("down_count", 0)) >= 6 and now - float(state.get("last_scale_down_ts", 0.0)) >= 180.0:
            new_r = max(1, new_r - 1)
            state["down_count"] = 0
            if new_r != prev_r:
                state["last_scale_down_ts"] = now

        if new_r != prev_r:
            state["R"] = new_r
            payload = {
                "previous_R": prev_r,
                "new_R": new_r,
                "K": int(state.get("K", 4)),
                "reason": "scale_up" if new_r > prev_r else "scale_down",
                "metrics": asdict(metrics),
            }
            self._emit(
                EventType.CAPACITY_SCALE_REQUESTED,
                idempotency_key=f"capacity:scale:{prev_r}:{new_r}:{int(now*1000)}",
                payload=payload,
            )
            events_emitted += 1

        state["updated_at"] = now
        self.save_state_atomic(state)

        capacity_state = CapacityState(
            mode=state["mode"],
            R=int(state["R"]),
            K=int(state.get("K", 4)),
            updated_at=float(state["updated_at"]),
        )
        return {
            "capacity_state": asdict(capacity_state),
            "events_emitted": events_emitted,
            "counters": {
                "up_count": int(state.get("up_count", 0)),
                "down_count": int(state.get("down_count", 0)),
                "critical_count": int(state.get("critical_count", 0)),
                "open_recover_count": int(state.get("open_recover_count", 0)),
            },
        }
