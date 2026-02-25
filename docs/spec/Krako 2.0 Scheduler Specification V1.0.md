# Krako 2.0 – Scheduler Specification (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the full production-level behavior of the Krako 2.0 Scheduler.

The Scheduler is the core execution engine inside the Data Plane.

It is responsible for:
- DAG execution
- WorkUnit placement
- Constraint enforcement
- Retry & timeout handling
- Privacy enforcement
- Backpressure & admission control

This specification is implementation-oriented and replaces draft versions.

---

# 1. Role in the System

Scheduler sits between:
- Gateway (TaskGraph ingress)
- Node Agents (CPU Nodes)
- LLM Pods (GPU endpoints)

It consumes TaskGraphs and produces execution outcomes.

Scheduler MUST NOT:
- Modify WorkUnit type
- Modify escalation logic
- Override privacy constraints
- Directly mutate billing or trust state

---

# 2. ExecutionSession Model

Each accepted TaskGraph creates one ExecutionSession.

ExecutionSession contains:
- execution_session_id
- graph_id
- tenant_id
- session_state
- WorkUnitExecution registry
- aggregate_metrics

Session States:
- initialized
- running
- completed
- failed
- cancelled

State transitions must be atomic and persisted.

---

# 3. WorkUnit Execution Lifecycle

States:
- queued
- ready
- dispatched
- running
- success
- failed
- timeout
- cancelled

Transition Rules:
1. WorkUnit moves to ready only when dependencies succeed.
2. dispatched only if substrate selected.
3. running only after execution begins.
4. success/failed/timeout are terminal states.

No WorkUnit may execute twice concurrently.

---

# 4. Placement Logic

Placement must satisfy ALL hard constraints:

- WorkUnit.type
- privacy
- trusted_node_required
- resource requirements
- region requirements

Mapping Rules:
- deterministic → CPU Node
- retrieval → CPU Node
- small_model → CPU Node
- llm → LLM Pod only

Hard Invariant:
llm WorkUnits must never execute on CPU Nodes.

Hard Invariant:
privacy=local_only must never route to LLM Pods.

---

# 5. Eligibility Evaluation

A WorkUnit becomes eligible when:

- All dependencies are in success state
- Graph not terminated
- Budget not already exceeded

Eligible units enter ready queue.

---

# 6. Scheduling Algorithm (Conceptual)

Baseline steps:

1. Identify eligible WorkUnits
2. Partition by substrate type
3. Filter candidates by constraints
4. Score candidates (availability, load, reputation)
5. Select best candidate
6. Dispatch WorkUnit

Scoring heuristics are implementation-private.

---

# 7. Retry Semantics

Retry allowed if:
- WorkUnit.idempotent = true
- error.retryable = true
- retry_count < max_attempts

Retries must:
- Preserve correlation ID
- Avoid duplicate billing
- Respect backoff policy

Retry state must be persisted.

---

# 8. Timeout Handling

Two timeout layers:

1. dispatch_timeout_ms
2. run_timeout_ms

If dispatch timeout:
- Try alternative placement
- Or fail if no candidate

If run timeout:
- Mark WorkUnit as timeout
- Apply retry policy

---

# 9. Backpressure & Admission Control

Scheduler must implement:

- Global concurrency caps
- Per-tenant concurrency caps
- Region-level queue limits
- LLM Pod saturation detection

Admission rejection reasons:
- RESOURCE_EXHAUSTED
- BUDGET_EXCEEDED
- REGION_UNAVAILABLE

Admission control must run BEFORE LLM invocation.

---

# 10. Privacy Enforcement

Privacy is enforced at placement time.

Rules:
- local_only → CPU Node within trusted boundary only
- allow_remote → LLM Pod allowed

Privacy violations are fatal errors.

Placement decisions must be logged.

---

# 11. Budget Enforcement

Budget types:
- max_tokens
- max_latency_ms
- max_cost_usd

Scheduler must:
- Reject execution if impossible to satisfy
- Stop further llm WorkUnits if token budget exhausted
- Emit budget_exceeded events

Scheduler must not silently ignore budget constraints.

---

# 12. Aggregation & Completion

When all terminal WorkUnits succeed:
- ExecutionSession → completed
- Emit ExecutionSessionCompleted event

If critical WorkUnit fails:
- ExecutionSession → failed

Non-critical failures follow graph-level policy.

---

# 13. Failure Handling

Failure Categories:
- Node failure
- Pod timeout
- Network partition
- Resource exhaustion

Scheduler must:
- Retry idempotent tasks
- Avoid retry storms
- Limit retry amplification

---

# 14. Concurrency Model

Scheduler must support:
- Multiple ExecutionSessions concurrently
- Parallel execution of independent WorkUnits

No shared mutable state between sessions.

---

# 15. Event Emission

Scheduler must emit:
- WorkUnitQueued
- WorkUnitDispatched
- WorkUnitStarted
- WorkUnitCompleted
- WorkUnitFailed
- WorkUnitRetried
- ExecutionSessionCompleted

Event delivery must be at-least-once.

---

# 16. Hard System Invariants

1. Escalation logic never modified in Data Plane
2. llm WorkUnits never run on CPU Nodes
3. privacy=local_only never routed to LLM Pod
4. No duplicate billing on retries
5. DAG acyclicity always enforced
6. No concurrent duplicate execution of same WorkUnit

These invariants must be covered by CI tests.

---

# 17. Non-Goals

Scheduler does NOT:
- Implement model optimization
- Implement billing logic
- Implement trust scoring
- Perform transformer-level parallelization

---

# Change Log

v1.0 – Full engineering rewrite replacing draft scheduler spec
