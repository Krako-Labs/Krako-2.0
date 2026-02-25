from __future__ import annotations

import os
import sys

from krako2.agent.agent import NodeAgent
from krako2.scheduler.node_registry import NodeRegistry


def main() -> int:
    node_id = os.getenv("NODE_ID")
    if not node_id:
        print("NODE_ID is required", file=sys.stderr)
        return 2

    data_dir = os.getenv("DATA_DIR", "data")
    poll_interval_ms = int(os.getenv("POLL_INTERVAL_MS", "500"))

    registry = NodeRegistry(registry_path=f"{data_dir}/node_registry.json")
    node_ids = {n.node_id for n in registry.list_nodes()}
    if node_id not in node_ids:
        print(f"NODE_ID not found in node registry: {node_id}", file=sys.stderr)
        return 2

    agent = NodeAgent(node_id=node_id, data_dir=data_dir, poll_interval_ms=poll_interval_ms)
    agent.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
