from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from krako2.agent.agent import NodeAgent

_SIX_DP = re.compile(r"^-?\d+\.\d{6}$")


def _append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def test_invocation_payload_includes_provider_and_estimated_cost(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("KRAKO_LLM_PROVIDER", "stub")

    events = tmp_path / "events.jsonl"
    _append_event(
        events,
        {
            "id": "dispatch-1",
            "type": "workunit.scheduled",
            "idempotency_key": "schedule:wu-1:1",
            "work_unit_id": "wu-1",
            "payload": {
                "selected_node_id": "node-1",
                "kind": "llm_pod",
                "prompt": "Tell me a joke about kraken.",
                "model": "stub-1",
                "simulated_ms": 0,
                "tenant_id": "tenant-a",
                "correlation_id": "sess:s1",
                "execution_session_id": "s1",
            },
        },
    )

    agent = NodeAgent(
        node_id="node-1",
        data_dir=tmp_path,
        event_log_path=events,
        state_path=tmp_path / "agent_state.json",
    )
    assert agent.poll_once()["processed"] == 1

    rows = _read_events(events)
    invocations = [e for e in rows if e.get("type") == "llm.invocation.completed"]
    assert len(invocations) == 1

    payload = invocations[0]["payload"]
    assert payload["provider"] == "stub"
    assert _SIX_DP.match(str(payload["estimated_cost_usd"]))


def test_e2e_demo_includes_latency_and_cost_fields(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "e2e_demo.py"
    out = subprocess.check_output(
        [
            sys.executable,
            str(script),
            "--data-dir",
            str(tmp_path),
            "--kind",
            "llm_pod",
            "--polls",
            "2",
            "--llm-provider",
            "stub",
            "--reset",
        ],
        text=True,
    )
    summary = json.loads(out)

    assert summary["llm_provider_used"] == "stub"
    assert isinstance(summary["llm_latency_ms_p50"], int)
    assert isinstance(summary["llm_latency_ms_p95"], int)
    assert _SIX_DP.match(str(summary["llm_estimated_cost_usd_total"]))
    assert summary["ledger_llm_total_usd"] != "0.000000"
