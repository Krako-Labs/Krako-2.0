# Krako 2.0 – KORA ↔ Krako Interface Specification

Version: v0.1
Status: Draft
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the interface contract between:

- KORA (Control Plane – execution intelligence)
- Krako 2.0 (Data Plane – distributed execution fabric)

This is one of the most critical boundaries in the system. It ensures:

- Clear separation of concerns
- No leakage of scheduling logic into KORA
- No semantic rewriting of intent inside Krako

---

# 1. Responsibility Boundary

## 1.1 KORA Responsibilities

KORA is responsible for:

- Generating TaskGraph (DAG)
- Creating WorkUnits
- Determining escalation (small → medium → large tier)
- Setting budgets (token, latency, cost hints)
- Setting privacy constraints
- Declaring idempotency and criticality

KORA does NOT:

- Decide node placement
- Manage distributed scheduling
- Perform retries
- Handle billing or reputation

---

## 1.2 Krako Responsibilities

Krako is responsible for:

- Validating TaskGraph schema
- Scheduling WorkUnits
- Enforcing constraints
- Handling retries and timeouts
- Routing llm WorkUnits to LLM Pods
- Aggregating results
- Emitting telemetry

Krako does NOT:

- Change WorkUnit type
- Invent new escalation decisions
- Override privacy constraints

---

# 2. Primary Interface: Submit TaskGraph

## 2.1 API Contract (Conceptual)

KORA → Krako

```json
{
  "task_graph": { ... },
  "submission_metadata": {
    "submitted_at": "timestamp",
    "kora_version": "string",
    "trace_id": "uuid"
  }
}
```

Krako → KORA

```json
{
  "status": "accepted",
  "execution_session_id": "uuid"
}
```

Possible statuses:
- accepted
- rejected_schema_invalid
- rejected_budget_invalid
- rejected_capacity

---

# 3. Validation Contract

Krako MUST validate:

- TaskGraph schema_version compatibility
- DAG acyclicity
- Unique WorkUnit IDs
- Dependency resolution

If validation fails:

Krako must return a structured error and not mutate the graph.

---

# 4. Escalation Integrity Rule

This is a core invariant.

If KORA produces a WorkUnit of type "llm":

Krako MUST:
- Route it only to LLM Pods
- Respect budget_tokens
- Respect privacy flags

Krako MUST NOT:
- Downgrade llm → small_model
- Upgrade small_model → llm
- Modify tier without explicit future policy flag

Escalation logic belongs exclusively to KORA.

---

# 5. Budget Propagation

KORA may specify:

- max_tokens (per WorkUnit)
- max_cost_usd (graph-level hint)
- max_latency_ms

Krako responsibilities:

- Enforce per-WorkUnit token limits (when reported by Pod)
- Reject execution if budget constraints are impossible to meet
- Emit telemetry for billing context

Krako MUST NOT silently ignore budget constraints.

---

# 6. Privacy Enforcement

KORA defines privacy constraints.

Krako enforces them.

If WorkUnit.constraint.privacy = local_only:
- Krako must restrict placement to trusted CPU Nodes
- Krako must not route to LLM Pods

If allow_remote:
- LLM Pod routing permitted

Violation of privacy constraint is a critical system error.

---

# 7. Feedback Channel (Execution Results)

Krako → KORA (optional integration layer)

KORA may subscribe to execution telemetry for:

- Confidence adjustment
- Policy tuning
- Escalation model improvement

This is asynchronous.

Example feedback event:

```json
{
  "execution_session_id": "uuid",
  "metrics": {
    "escalation_rate": 0.42,
    "avg_latency_ms": 1800
  }
}
```

Krako does not require KORA feedback for correctness.

---

# 8. Error Propagation

If a WorkUnit fails irrecoverably:

Krako returns:

```json
{
  "execution_session_id": "uuid",
  "status": "failed",
  "reason": "WORK_UNIT_FAILED",
  "work_unit_id": "uuid"
}
```

KORA may choose to:
- Retry full graph
- Adjust policy
- Escalate further

Krako does not auto-modify the graph.

---

# 9. Version Compatibility

Both sides must declare version.

Compatibility rules:

- KORA version >= minimum supported
- TaskGraph schema_version supported by Krako

Breaking changes require version negotiation.

---

# 10. Non-Goals

This interface does NOT:

- Define scheduler internal heuristics
- Define billing logic
- Define trust scoring
- Define model internals

It only defines the boundary between intelligence and execution.

---

# Change Log

## v0.1 (2026-02-25)
- Initial KORA ↔ Krako Interface Specification created
- Defined responsibility boundary, submission contract, escalation integrity, and privacy enforcement rules

