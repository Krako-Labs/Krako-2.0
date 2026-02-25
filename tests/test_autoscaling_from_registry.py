from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from krako2.autoscaling.metrics import compute_metrics_from_registry
from krako2.scheduler.node_registry import Node


def test_compute_metrics_from_registry_scales_queue_depth() -> None:
    nodes = [
        Node(
            node_id="node-1",
            enabled=True,
            health_status="healthy",
            supported_kinds=["cpu"],
            available_concurrency=4,
            active_queue_depth=5,
            utilization=0.4,
            trust_score=0.7,
            region="eu-west",
            version="0.1.0",
        )
    ]

    metrics = compute_metrics_from_registry(nodes)
    assert metrics.queue_depth >= 500
    assert 0.0 <= metrics.utilization <= 1.0


def _run_demo(script: Path, data_dir: Path, burst: int, polls: int) -> dict:
    cmd = [
        sys.executable,
        str(script),
        "--data-dir",
        str(data_dir),
        "--simulate-pressure",
        "auto",
        "--burst",
        str(burst),
        "--polls",
        str(polls),
        "--reset",
    ]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def test_e2e_auto_autoscaling_emits_events_under_burst(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "e2e_demo.py"
    summary = _run_demo(script, tmp_path, burst=3, polls=6)

    assert summary["autoscaling"]["events_emitted_total"] > 0


def test_auto_mode_can_enter_throttled(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "e2e_demo.py"
    summary = _run_demo(script, tmp_path, burst=6, polls=12)

    mode = summary["autoscaling"]["capacity_state"]["mode"]
    replicas = int(summary["autoscaling"]["capacity_state"]["R"])
    assert mode in {"THROTTLED", "CRITICAL"} or replicas > 1
