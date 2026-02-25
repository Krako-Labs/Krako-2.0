from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _claim_key(work_unit_id: str, dispatch_event_id: str) -> str:
    return f"{work_unit_id}:{dispatch_event_id}"


def _default_index() -> dict[str, Any]:
    return {
        "version": "0.1",
        "generated_at": _utc_now_iso(),
        "claims": {},
    }


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_index(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return _default_index()
    try:
        with p.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid claim index JSON: {p}") from exc
    except OSError as exc:
        raise ValueError(f"failed reading claim index: {p}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"invalid claim index schema: {p}")
    claims = raw.get("claims")
    if not isinstance(claims, dict):
        raise ValueError(f"invalid claim index claims map: {p}")

    normalized_claims: dict[str, dict[str, str]] = {}
    for k, v in claims.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        normalized_claims[k] = {
            "node_id": str(v.get("node_id", "")),
            "claim_event_id": str(v.get("claim_event_id", "")),
            "ts": str(v.get("ts", "")),
        }

    return {
        "version": str(raw.get("version", "0.1")),
        "generated_at": str(raw.get("generated_at", _utc_now_iso())),
        "claims": normalized_claims,
    }


def is_claimed(path: str | Path, work_unit_id: str, dispatch_event_id: str) -> bool:
    idx = load_index(path)
    return _claim_key(work_unit_id, dispatch_event_id) in idx["claims"]


def record_claim(
    path: str | Path,
    work_unit_id: str,
    dispatch_event_id: str,
    node_id: str,
    claim_event_id: str,
    ts_iso: str,
) -> None:
    p = Path(path)
    try:
        idx = load_index(p)
    except ValueError:
        idx = _default_index()

    key = _claim_key(work_unit_id, dispatch_event_id)
    claims: dict[str, dict[str, str]] = idx.setdefault("claims", {})
    if key not in claims:
        claims[key] = {
            "node_id": str(node_id),
            "claim_event_id": str(claim_event_id),
            "ts": str(ts_iso),
        }
    idx["version"] = "0.1"
    idx["generated_at"] = _utc_now_iso()
    _atomic_write(p, idx)


def rebuild_from_event_log(index_path: str | Path, event_log_path: str | Path) -> dict[str, Any]:
    claims: dict[str, dict[str, str]] = {}
    event_path = Path(event_log_path)
    if event_path.exists():
        with event_path.open("r", encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if not text:
                    continue
                try:
                    event = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("type") != "workunit.claimed":
                    continue
                payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                work_unit_id = str(payload.get("work_unit_id", event.get("work_unit_id", "")))
                dispatch_event_id = str(payload.get("dispatch_event_id", ""))
                if not work_unit_id or not dispatch_event_id:
                    continue
                key = _claim_key(work_unit_id, dispatch_event_id)
                if key in claims:
                    continue
                claims[key] = {
                    "node_id": str(payload.get("node_id", "")),
                    "claim_event_id": str(event.get("id", "")),
                    "ts": str(event.get("created_at", _utc_now_iso())),
                }

    idx = {
        "version": "0.1",
        "generated_at": _utc_now_iso(),
        "claims": claims,
    }
    _atomic_write(Path(index_path), idx)
    return idx
