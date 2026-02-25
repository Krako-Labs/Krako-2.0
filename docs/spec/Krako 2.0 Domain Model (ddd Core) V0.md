# Krako 2.0 – Domain Model (DDD Core)

Version: v0.1
Status: Draft
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines Krako 2.0’s domain model using Domain-Driven Design (DDD) at a practical level.

Goals:
- Fix system boundaries (bounded contexts)
- Establish ubiquitous language
- Define key aggregates/entities/value objects
- Define context relationships and key domain events

Non-goal:
- Provide a complete enterprise DDD playbook

---

# 1. Ubiquitous Language (Core Terms)

These terms must be used consistently across docs, code, and conversations.

- Request: a user/app-level invocation that triggers execution
- Task Graph (TaskGraph): a DAG produced by KORA describing execution
- Work Unit (WorkUnit): minimal schedulable unit executed by Krako
- Execution: running WorkUnits to completion under constraints
- Escalation: routing from structured execution to LLM Pod
- LLM Pod: GPU-backed regional endpoint for large-model execution
- CPU Node: heterogeneous contributor device running Node Agent
- Node Agent: runtime on CPU Node that executes WorkUnits
- Placement: selecting where a WorkUnit runs
- Constraints: latency/privacy/budget requirements attached to WorkUnits
- Budget: cost envelope (tokens, dollars, time) associated with a Request
- Telemetry: execution events, logs, metrics emitted by runtime
- Metering: accounting of token usage, latency, and billable units
- Credit: pre-paid unit of value used for paid execution (especially Pods)
- Reputation: trust score for Nodes used for placement/weighting

---

# 2. Bounded Contexts

Krako 2.0 comprises multiple bounded contexts. Each context owns its data model and invariants.

## 2.1 Routing Context (KORA)

Owns:
- TaskGraph generation
- Escalation policy
- Deterministic-first planning
- Budget propagation (as hints/constraints)

Primary outputs:
- TaskGraph
- WorkUnits

Primary events:
- TaskGraphCreated

---

## 2.2 Execution Context (Krako Core)

Owns:
- WorkUnit scheduling and execution lifecycle
- Dependency resolution (DAG execution)
- Placement decisions (baseline)
- Retries/timeouts
- Result aggregation (deterministic)

Primary entities:
- ExecutionSession
- WorkUnitExecution

Primary events:
- WorkUnitDispatched
- WorkUnitCompleted
- WorkUnitFailed

---

## 2.3 Node Context (Network)

Owns:
- CPU Node identity
- Capabilities
- Availability/health
- Agent versions

Primary entities:
- Node
- NodeCapability

Primary events:
- NodeRegistered
- NodeHeartbeat
- NodeRemoved

---

## 2.4 Pod Context (LLM Pods)

Owns:
- LLM Pod endpoints
- Model catalog (public interface)
- Pod health/region
- Token usage reporting

Primary entities:
- Pod
- ModelTier

Primary events:
- PodReady
- PodDegraded
- LLMWorkUnitCompleted

---

## 2.5 Billing Context (Commercial)

Owns:
- Credits
- Pricing rules
- Metering aggregation
- Invoicing
- Rev-share

Primary entities:
- Account
- CreditWallet
- UsageRecord

Primary events:
- CreditsDebited
- UsageRecorded
- InvoiceIssued

---

## 2.6 Trust Context (Security & Reputation)

Owns:
- Node reputation
- Anomaly detection signals
- Slashing/penalties
- Attestation mechanisms (implementation-specific)

Primary entities:
- ReputationScore
- TrustSignal

Primary events:
- ReputationUpdated
- NodeSlashed

---

# 3. Context Map (Relationships)

## 3.1 High-Level Flow

Routing Context (KORA)
  → publishes TaskGraph
Execution Context (Krako)
  → consumes TaskGraph and executes WorkUnits
Node Context
  → supplies Node availability/capabilities to Execution Context
Pod Context
  → supplies Pod availability/models to Execution Context
Execution Context
  → emits Telemetry events
Billing Context
  → consumes usage telemetry for metering/credits
Trust Context
  → consumes execution outcomes to update reputation

## 3.2 Integration Style

- KORA → Krako: Published Language (TaskGraph + WorkUnit schema)
- Krako ↔ Node Agent: Contract-based protocol
- Krako ↔ Pods: Contract-based protocol
- Krako → Billing: Event-driven (UsageRecorded)
- Krako → Trust: Event-driven (ExecutionOutcome)

---

# 4. Aggregates, Entities, Value Objects

## 4.1 Routing Context (KORA)

### Aggregate: TaskGraph
Invariants:
- Graph must be acyclic
- All WorkUnits have unique IDs within graph
- Dependencies reference existing WorkUnits

Entities:
- WorkUnit (definition)

Value Objects:
- ConstraintSet (latency/privacy/budget)
- EscalationPolicy

---

## 4.2 Execution Context (Krako)

### Aggregate: ExecutionSession
Represents the lifecycle of executing one TaskGraph.

Invariants:
- Session references exactly one TaskGraph
- WorkUnitExecution transitions follow allowed state machine
- Results are immutable once committed

Entities:
- WorkUnitExecution
- ExecutionState

Value Objects:
- PlacementDecision
- RetryPolicy
- TimeoutPolicy

---

## 4.3 Node Context

### Aggregate: Node
Invariants:
- Node identity is stable
- Capability set is versioned

Entities:
- NodeCapability
- NodeHealth

Value Objects:
- Region
- NodeType

---

## 4.4 Pod Context

### Aggregate: Pod
Invariants:
- Pod belongs to a region
- Pod exposes supported models and constraints

Entities:
- ModelOffering

Value Objects:
- ModelTier (small/medium/large)
- PodEndpoint

---

## 4.5 Billing Context

### Aggregate: Account
Invariants:
- Usage must be tied to an account
- Credits cannot go negative (unless overdraft explicitly allowed)

Entities:
- CreditWallet
- UsageRecord

Value Objects:
- Price
- TokenCount

---

## 4.6 Trust Context

### Aggregate: ReputationProfile
Invariants:
- Reputation updates are monotonic within a time window (configurable)
- Slashing requires evidence record

Entities:
- ReputationScore
- TrustSignal

Value Objects:
- Confidence
- Evidence

---

# 5. Domain Events (Canonical)

## 5.1 Routing Events
- TaskGraphCreated(graph_id, request_id)

## 5.2 Execution Events
- ExecutionSessionStarted(session_id, graph_id)
- WorkUnitQueued(work_unit_id)
- WorkUnitDispatched(work_unit_id, node_id|pod_id)
- WorkUnitCompleted(work_unit_id, duration_ms)
- WorkUnitFailed(work_unit_id, reason)
- ExecutionSessionCompleted(session_id)

## 5.3 Node Events
- NodeRegistered(node_id, region, capabilities)
- NodeHeartbeat(node_id, health)

## 5.4 Pod Events
- PodReady(pod_id, region)
- LLMWorkUnitCompleted(work_unit_id, tokens_in, tokens_out)

## 5.5 Billing Events
- UsageRecorded(account_id, work_unit_id, billable_units)
- CreditsDebited(account_id, amount)

## 5.6 Trust Events
- ReputationUpdated(node_id, score)
- NodeSlashed(node_id, reason)

---

# 6. State Machines

## 6.1 WorkUnitExecution State

States:
- queued → dispatched → running → success
- queued → dispatched → running → failed
- queued → timeout

Rules:
- A WorkUnit may not be dispatched before dependencies succeed (unless marked as speculative)
- A WorkUnit may be retried only if idempotent=true

---

# 7. Boundary Decisions (Important)

## 7.1 Control vs Data Plane

- Control Plane (KORA) decides: what to do, escalation, budgets
- Data Plane (Krako) decides: where to run, how to retry, how to keep system reliable

Scheduler MUST NOT change semantic intent (e.g., turning an llm WorkUnit into a small_model WorkUnit).

## 7.2 Billing and Trust are separate

- Execution emits events
- Billing/Trust consume events

Do not embed billing or reputation logic inside execution core.

---

# Change Log

## v0.1 (2026-02-25)
- Initial DDD domain model created
- Defined bounded contexts, aggregates, and canonical events

