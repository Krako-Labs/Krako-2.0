from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class RetryBudgetStore:
    def __init__(
        self,
        state_path: str | Path = "data/retry_budget_state.json",
        capacity: float = 40.0,
        refill_tokens_per_min: float = 20.0,
    ) -> None:
        self.state_path = Path(state_path)
        self.capacity = float(capacity)
        self.refill_per_second = float(refill_tokens_per_min) / 60.0
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_path.exists():
            self._atomic_write({"tenants": {}})

    def _read(self) -> dict[str, Any]:
        with self.state_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _atomic_write(self, data: dict[str, Any]) -> None:
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_path)

    def _refill(self, tenant: dict[str, float], now: float) -> dict[str, float]:
        last = float(tenant.get("last_refill_ts", now))
        tokens = float(tenant.get("tokens", self.capacity))
        elapsed = max(0.0, now - last)
        refilled = min(self.capacity, tokens + elapsed * self.refill_per_second)
        return {"tokens": refilled, "last_refill_ts": now}

    def allow_retry(self, tenant_id: str) -> bool:
        now = time.time()
        state = self._read()
        tenants = state.setdefault("tenants", {})
        tenant = tenants.get(tenant_id, {"tokens": self.capacity, "last_refill_ts": now})
        tenant = self._refill(tenant, now)

        allowed = tenant["tokens"] >= 1.0
        if allowed:
            tenant["tokens"] -= 1.0

        tenants[tenant_id] = tenant
        self._atomic_write(state)
        return allowed

    def peek(self, tenant_id: str) -> dict[str, float]:
        now = time.time()
        state = self._read()
        tenants = state.setdefault("tenants", {})
        tenant = tenants.get(tenant_id, {"tokens": self.capacity, "last_refill_ts": now})
        tenant = self._refill(tenant, now)
        tenants[tenant_id] = tenant
        self._atomic_write(state)
        return {
            "tokens": float(tenant["tokens"]),
            "capacity": float(self.capacity),
            "refill_tokens_per_min": float(self.refill_per_second * 60.0),
        }
