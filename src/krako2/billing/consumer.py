from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from krako2.billing.money import dec, quant6, serialize_decimal
from krako2.billing.storage import BillingDedupeStore, BillingLedgerWriter
from krako2.domain.models import Event


class BillingConsumer:
    def __init__(
        self,
        ledger_path: str | Path = "data/billing_ledger.jsonl",
        dedupe_path: str | Path = "data/billing_dedupe.json",
    ) -> None:
        self.ledger = BillingLedgerWriter(ledger_path)
        self.dedupe = BillingDedupeStore(dedupe_path)

        self.cpu_unit_price = dec(os.getenv("KRAKO_CPU_USD_PER_SEC", "0.000500"))
        self.llm_unit_price_per_1k = dec(os.getenv("KRAKO_LLM_USD_PER_1K_TOKENS", "0.002000"))

    def _parse_cpu_seconds(self, payload: dict[str, Any]) -> Decimal | None:
        raw = payload.get("cpu_seconds")
        if raw is None:
            return None
        try:
            return dec(str(raw))
        except Exception:
            return None

    def _parse_llm_tokens(self, payload: dict[str, Any]) -> int | None:
        raw = payload.get("llm_tokens")
        if raw is None:
            return None
        try:
            value = int(raw)
            if value < 0:
                return None
            return value
        except Exception:
            return None

    def _build_record(self, event: Event) -> dict[str, Any] | None:
        payload = event.payload or {}
        cpu_seconds = self._parse_cpu_seconds(payload)
        llm_tokens = self._parse_llm_tokens(payload)

        # v0.1: payload.amount is intentionally ignored.
        if cpu_seconds is None and llm_tokens is None:
            return None

        if cpu_seconds is None:
            cpu_seconds = dec("0")
        if llm_tokens is None:
            llm_tokens = 0

        subtotal_cpu = quant6(cpu_seconds * self.cpu_unit_price)
        subtotal_llm = quant6((dec(llm_tokens) / dec("1000")) * self.llm_unit_price_per_1k)
        total = quant6(subtotal_cpu + subtotal_llm)

        tenant_id = str(payload.get("tenant_id", "default"))
        correlation_id = str(payload.get("correlation_id", event.idempotency_key))

        return {
            "event_id": event.id,
            "event_type": event.type.value,
            "work_unit_id": event.work_unit_id,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id,
            "cpu_seconds": serialize_decimal(cpu_seconds),
            "llm_tokens": llm_tokens,
            "cpu_unit_price_usd": serialize_decimal(self.cpu_unit_price),
            "llm_unit_price_usd_per_1k": serialize_decimal(self.llm_unit_price_per_1k),
            "subtotal_cpu_usd": serialize_decimal(subtotal_cpu),
            "subtotal_llm_usd": serialize_decimal(subtotal_llm),
            "total_usd": serialize_decimal(total),
            "currency": "USD",
            "rounded_scale": 6,
            "rounding_mode": "ROUND_HALF_EVEN",
            "pricing_version": "0.1",
        }

    def consume(self, event: Event) -> bool:
        if self.dedupe.has(event.id):
            return False

        record = self._build_record(event)
        if record is None:
            return False

        self.ledger.append(record)
        self.dedupe.mark_processed(event.id)
        return True
