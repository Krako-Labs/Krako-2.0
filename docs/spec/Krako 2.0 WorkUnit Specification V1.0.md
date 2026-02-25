# Krako 2.0 – WorkUnit Specification (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the WorkUnit contract – the smallest schedulable execution unit in Krako 2.0.

The WorkUnit is the atomic boundary between:
- Control Plane (KORA)
- Data Plane (Krako Scheduler)
- Execution Substrates (CPU Nodes / LLM Pods)

This specification is authoritative and implementation-oriented.

---

# 1. Conceptual Model

A WorkUnit represents one bounded computation step inside a TaskGraph.

Properties:
- Self-contained
- Deterministically typed
- Constraint-bound
- Auditable
- Retry-aware

A WorkUnit must be small enough to:
- Be independently scheduled
- Be retried safely (if idempotent)
- Be verified

---

# 2. WorkUnit Types

Allowed types (v1.0):

## 2.1 deterministic

Pure logic operations.
Examples:
- parsing
- normalization
- validation
- schema enforcement
- policy evaluation

Execution substrate:
- CPU Node only

Constraints:
- Must be deterministic
- Must not perform network I/O unless explicitly allowed

---

## 2.2 retrieval

Structured lookup operations.
Examples:
- vector search
- index lookup
- ranking
- knowledge graph traversal

Execution substrate:
- CPU Node only

Security note:
- Retrieval outputs must be treated as untrusted input for downstream tasks.

---

## 2.3 small_model

Local or lightweight model inference.
Examples:
- classification
- extraction
- routing assistance

Execution substrate:
- CPU Node

Constraints:
- Must not require GPU
- Must respect local memory limits

---

## 2.4 llm

Large-model generative inference.

Execution substrate:
- LLM Pod only

Hard rule:
- llm WorkUnits MUST NEVER execute on CPU Nodes.

---

# 3. Canonical JSON Contract

```json
{
  "id": "uuid",
  "graph_id": "uuid",
  "type": "deterministic | retrieval | small_model | llm",
  "name": "string",
  "dependencies": ["uuid"],
  "input": {},
  "constraints": {
    "latency_ms": 200,
    "budget_tokens": 0,
    "privacy": "local_only | allow_remote",
    "trusted_node_required": false
  },
  "execution_hint": {
    "preferred_substrate": "cpu | llm_pod",
    "region": "string",
    "node_tags": ["string"],
    "requires": {
      "min_ram_mb": 0,
      "min_vram_mb": 0,
      "accelerators": []
    }
  },
  "idempotent": true,
  "critical": true,
  "verification_mode": "none | schema | quorum | recompute",
  "timeouts": {
    "dispatch_timeout_ms": 2000,
    "run_timeout_ms": 5000
  },
  "retries": {
    "max_attempts": 2,
    "backoff_ms": 200
  }
}
```

---

# 4. Field Semantics

## 4.1 id
Unique within TaskGraph.

## 4.2 dependencies
Must reference valid WorkUnits.
Cannot reference itself.

## 4.3 constraints
Hard requirements enforced by Scheduler.

### latency_ms
Maximum acceptable execution latency.

### budget_tokens
Applies to small_model and llm types.
Hard limit for LLM invocation.

### privacy
local_only:
- Must execute only on trusted CPU Nodes.

allow_remote:
- May be routed to LLM Pod.

### trusted_node_required
If true:
- Only nodes within trusted boundary may execute.

---

## 4.4 execution_hint
Advisory placement preferences.
Scheduler may override hints if constraints still satisfied.

---

## 4.5 idempotent
If true:
- Safe to retry without side effects.

If false:
- Retry must be limited.

---

## 4.6 critical
If true:
- Failure fails entire TaskGraph (unless policy overrides).

If false:
- Failure may not terminate graph.

---

## 4.7 verification_mode
Defines post-execution verification strategy.

none – no additional verification
schema – output schema validation
quorum – multiple nodes execute and results compared
recompute – independent recomputation for validation

---

# 5. WorkUnitResult Contract

```json
{
  "work_unit_id": "uuid",
  "status": "success | failed | timeout",
  "started_at": "timestamp",
  "finished_at": "timestamp",
  "duration_ms": 0,
  "output": {},
  "usage": {
    "tokens_in": 0,
    "tokens_out": 0,
    "cost_usd": 0.0
  },
  "execution": {
    "node_id": "string",
    "pod_id": "string|null",
    "region": "string"
  },
  "error": null
}
```

---

# 6. Error Classification

Allowed error codes:

- VALIDATION_ERROR
- EXECUTION_ERROR
- TIMEOUT
- RESOURCE_EXHAUSTED
- NETWORK_ERROR
- AUTH_ERROR
- RATE_LIMITED
- UNSUPPORTED

Retryable only if:
- error.retryable = true
- idempotent = true

---

# 7. Execution Rules

1. WorkUnit cannot execute until dependencies succeed.
2. Scheduler must respect type → substrate mapping.
3. privacy constraints must be enforced at scheduling.
4. Retry must preserve correlation identifiers.
5. No duplicate billing on retry.

---

# 8. Hard Invariants

1. llm WorkUnits never execute on CPU nodes.
2. privacy=local_only never routed to LLM Pods.
3. WorkUnit id uniqueness enforced.
4. DAG dependencies satisfied before execution.
5. No double billing on retries.

These invariants must be enforced via CI tests.

---

# 9. Non-Goals

This specification does NOT:
- Define scheduler heuristics
- Define billing calculations
- Define trust scoring algorithms
- Define model internals

---

# Change Log

v1.0 – Initial full engineering version

