# Krako 2.0 – System Architecture Specification (Full Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the full working system architecture of Krako 2.0 at an engineering level.

It is intended to:
- Guide implementation
- Define strict boundaries between subsystems
- Prevent architectural drift
- Provide executable invariants
- Serve as the single source of truth for system design

This document is NOT marketing-oriented.

---

# 1. System Definition

Krako 2.0 is a heterogeneous AI execution fabric.

It separates execution intelligence (Control Plane) from distributed execution infrastructure (Data Plane), and centralizes memory-bound generative inference inside LLM Pods.

Krako 2.0 performs:
- Structured task decomposition
- Distributed micro-task scheduling
- Privacy-aware placement
- Budget-constrained execution
- Event-driven billing and trust processing

Krako 2.0 does NOT:
- Distribute transformer layers
- Federate KV cache
- Parallelize token generation across WAN nodes

---

# 2. Architectural Layers

## 2.1 Application Layer

External clients:
- AI applications
- SDK integrations
- KORA Studio

Responsibilities:
- Submit high-level execution requests
- Receive final response

Applications never directly control placement.

---

## 2.2 Control Plane (KORA)

KORA responsibilities:
- Convert request → TaskGraph (DAG)
- Decompose into WorkUnits
- Assign execution type
- Define escalation logic
- Attach constraints (privacy, budget, latency)
- Declare idempotency and criticality

KORA produces:
- TaskGraph object

KORA does NOT:
- Perform scheduling
- Handle retries
- Manage node health
- Manage billing or trust

Control Plane is logically stateless relative to distributed execution.

---

## 2.3 Data Plane (Krako Fabric)

The Data Plane executes TaskGraphs at scale.

Components:
- Gateway
- Scheduler
- ExecutionSession Manager
- Node Registry
- Result Aggregator
- Telemetry Publisher

Data Plane guarantees:
- Semantic integrity of WorkUnits
- Enforcement of constraints
- Deterministic dependency resolution

---

## 2.4 Execution Substrates

### CPU Nodes
Execute:
- deterministic
- retrieval
- small_model

Characteristics:
- Heterogeneous
- May be unreliable
- Bounded memory and CPU

### LLM Pods
Execute:
- llm WorkUnits

Characteristics:
- GPU-backed
- Memory-bandwidth-bound execution
- Regional
- Session-isolated
- KV cache local only

---

# 3. Core Runtime Model

## 3.1 ExecutionSession

Each TaskGraph submission creates an ExecutionSession.

ExecutionSession contains:
- graph_id
- execution_session_id
- session_state
- WorkUnitExecution map
- aggregated results

ExecutionSession states:
- initialized
- running
- completed
- failed
- cancelled

---

## 3.2 WorkUnit Lifecycle

WorkUnitExecution states:
- queued
- ready
- dispatched
- running
- success
- failed
- timeout
- cancelled

State transitions must be atomic and persisted.

No WorkUnit may execute unless all dependencies are in success state.

---

# 4. Scheduler Design

## 4.1 Eligibility Rules

A WorkUnit becomes eligible when:
- All dependencies succeeded
- Graph not terminated
- Budget not exceeded

Eligible WorkUnits enter ready state.

---

## 4.2 Placement Rules

Placement must satisfy:
- WorkUnit.type
- privacy constraint
- resource requirements
- region constraint
- availability

Hard Rules:
- llm type → LLM Pod only
- privacy=local_only → CPU node within trust boundary only
- Scheduler must never rewrite WorkUnit type

---

## 4.3 Retry Semantics

Retry allowed if:
- idempotent = true
- retryable error
- retry count < max_attempts

Retry must preserve:
- correlation id
- billing id

Retries must not double-bill.

---

## 4.4 Backpressure & Admission

Scheduler must implement:
- Global concurrency caps
- Per-tenant rate limits
- Region-based queue partitioning
- Circuit breaker for degraded Pods

Admission rejection codes:
- RESOURCE_EXHAUSTED
- BUDGET_EXCEEDED
- REGION_UNAVAILABLE

---

# 5. Result Aggregation

Aggregator responsibilities:
- Collect WorkUnit outputs
- Apply deterministic merge rules
- Emit final response

Aggregator must not:
- Execute new WorkUnits
- Modify semantic output beyond merge policy

---

# 6. Privacy Enforcement

Privacy enforcement occurs at scheduling time.

Constraints:
- local_only → CPU nodes with trusted flag
- allow_remote → Pod allowed

Scheduler must log placement decisions with privacy metadata.

Violation of privacy constraint is fatal.

---

# 7. Budget Enforcement

Budgets include:
- max_tokens
- max_latency_ms
- optional max_cost

Budget enforcement:
- Pre-invocation check before LLM call
- Soft checks for CPU tasks
- Hard fail if impossible to satisfy

---

# 8. Telemetry & Event Emission

All execution stages emit structured events.

Events include:
- WorkUnitDispatched
- WorkUnitStarted
- WorkUnitCompleted
- WorkUnitFailed
- LLMInvocationCompleted
- ExecutionSessionCompleted

Event delivery model:
- At-least-once
- Idempotent consumer required

---

# 9. Trust Model Integration

Trust Context consumes:
- WorkUnitCompleted
- WorkUnitFailed
- NodeHeartbeat

Scheduler may use reputation score for placement weighting.
Scheduler does not compute reputation.

---

# 10. Billing Integration

Billing Context consumes:
- token usage events
- CPU duration metrics

Execution layer does not debit credits.
Billing layer applies pricing and updates wallet.

---

# 11. Failure Modes

Major failure categories:
- Node failure
- Pod timeout
- Network partition
- Scheduler overload

System must:
- Retry idempotent tasks
- Fail-fast critical tasks
- Avoid escalation drift

---

# 12. Scaling Strategy

Scaling vectors:
- Increase CPU nodes
- Add regions
- Add LLM Pods
- Horizontal scheduler scaling

Scheduler must support stateless scaling with shared state backend.

---

# 13. Hard System Invariants

1. Escalation logic defined only by Control Plane
2. llm WorkUnits never run on CPU nodes
3. local_only never routed to LLM Pod
4. No double billing on retry
5. DAG acyclicity always enforced
6. KV cache never distributed across nodes

These invariants must be enforced via CI tests.

---

# 14. Open vs Private Boundary

Open components:
- WorkUnit schema
- TaskGraph schema
- Node Agent reference
- SDK

Private components:
- Production scheduler heuristics
- Placement scoring
- Billing engine
- Reputation algorithms
- Pod autoscaling

---

# Change Log

v1.0 – Full engineering rewrite replacing draft architecture

