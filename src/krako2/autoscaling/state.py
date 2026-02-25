from __future__ import annotations

import json
from pathlib import Path


def load_capacity_mode(state_path: Path) -> str:
    try:
        if not state_path.exists():
            return "OPEN"
        with state_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        mode = str(data.get("mode", "OPEN")).upper()
        if mode in {"OPEN", "THROTTLED", "CRITICAL"}:
            return mode
        return "OPEN"
    except Exception:
        return "OPEN"
