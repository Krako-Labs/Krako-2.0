# Krako 2.0 – Task Graph Specification (Full Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the complete Task Graph contract used between KORA (Control Plane) and Krako 2.0 (Data Plane).

The TaskGraph is the canonical execution blueprint for the distributed system.
It defines structure, invariants, execution semantics, and boundary guarantees.

This document is implementation-oriented and replaces earlier draft versions.

---

# 1. Conceptual Model

A TaskGraph is a Directed Acyclic Graph (DAG) composed of WorkUnits.

Each TaskGraph:
- Represents one execution request
- Is immutable once accepted by Krako
- Is versioned
- Contains graph-level constraints and policies

KORA is the sole producer of TaskGraphs.
Krako is the sole executor.

---

# 2. Structural Properties

## 2.1 Required Fields

Every TaskGraph MUST include:

- schema_version
- graph_version
- graph_id
- request_id
- tenant_id
- created_at
- work_units

---

## 2.2 Canonical JSON Schema

```json
{
  "schema_version": "1.0",
  "graph_version": "1",
  "graph_id": "uuid",
  "request_id": "uuid",
  "tenant_id": "string",
  "created_at": "timestamp",
  "budgets": {
    "max_latency_ms": 3000,
    "max_tokens": 6000,
    "max_cost_usd": 0.05
  },
  "policies": {
    "failure_policy": "fail_fast",
    "privacy_default": "allow_remote",
    "max_llm_invocations_per_session": 5
  },
  "work_units": [],
  "outputs": {
    "final": {
      "work_unit_id": "uuid",
      "selector": "output"
    }
  }
}
```

---

# 3. Invariants

A TaskGraph is valid only if:

1. The graph is acyclic.
2. All WorkUnit IDs are unique.
3. All dependencies reference existing WorkUnits.
4. All WorkUnits declare a valid type.
5. graph_version and schema_version are present.
6. Budgets are non-negative.

Violation of invariants must result in rejection before execution.

---

# 4. Execution Semantics

## 4.1 Dependency Resolution

A WorkUnit may transition to ready state only when:

- All dependencies are in success state
- Graph has not failed or been cancelled

No speculative execution in v1.0.

---

## 4.2 Graph Completion

A TaskGraph is considered complete when:

- All terminal WorkUnits succeed
OR
- failure_policy triggers termination

Terminal WorkUnits are those not referenced by any other WorkUnit.

---

# 5. Failure Policies

Allowed graph-level failure_policy values:

- fail_fast
- continue_on_error

Escalation must be pre-defined by KORA as explicit WorkUnits.
Krako must not invent new escalation steps.

---

# 6. Budget Semantics

Budgets are enforcement hints passed to Krako.

## 6.1 max_latency_ms
Soft constraint guiding placement.

## 6.2 max_tokens
Hard upper bound for LLM WorkUnits.

## 6.3 max_cost_usd
Billing-level constraint. Enforcement may be pre- or post-execution depending on configuration.

If budget cannot be satisfied, Scheduler must reject before execution.

---

# 7. Output Contract

The outputs section defines how the final response is constructed.

v1.0 supports:
- Selecting a single WorkUnit output via selector.

Future versions may include:
- Merge strategies
- Multi-output streaming
- Incremental output

---

# 8. Validation Checklist (Mandatory)

Before accepting a TaskGraph, Krako MUST validate:

- schema_version compatibility
- graph_version presence
- DAG acyclicity
- Dependency resolution
- Unique WorkUnit IDs
- Budget sanity

Validation failure results in rejection.

---

# 9. Security Considerations

TaskGraph must be treated as untrusted input.

Validation must include:
- Max graph size
- Max WorkUnit count
- Max depth limit

Protection against graph bombs is mandatory.

---

# 10. Versioning Policy

schema_version follows semantic versioning.

Breaking changes require:
- Major version increment
- Explicit compatibility mapping

Krako may support multiple schema versions simultaneously.

---

# 11. Non-Goals

This specification does NOT:
- Define scheduler heuristics
- Define transformer-level behavior
- Define distributed KV cache

---

# Change Log

v1.0 – Full engineering rewrite replacing draft v0.1

