from __future__ import annotations

from krako2.autoscaling.controller import Metrics
from krako2.scheduler.node_registry import Node


def compute_metrics_from_registry(nodes: list[Node]) -> Metrics:
    enabled = [n for n in nodes if n.enabled]
    if not enabled:
        return Metrics(queue_depth=0, w95_wait_s=0.0, utilization=0.0)

    avg_q = sum(int(n.active_queue_depth) for n in enabled) / len(enabled)
    queue_depth = int(avg_q * 100)

    avg_util = sum(float(n.utilization) for n in enabled) / len(enabled)
    utilization = max(0.0, min(1.0, avg_util))

    w95_wait_s = max(0.0, queue_depth / 200.0)
    return Metrics(queue_depth=queue_depth, w95_wait_s=w95_wait_s, utilization=utilization)
