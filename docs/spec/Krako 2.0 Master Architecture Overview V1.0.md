# Krako 2.0 – Master Architecture Overview

Version: v1.0
Status: Full Architecture Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document provides a complete architectural blueprint of Krako 2.0.

It integrates:

- Vision & Positioning
- System Architecture
- Domain Model (DDD)
- Task Graph & WorkUnit Contracts
- Scheduler Semantics
- Node & Trust Model
- LLM Pod Model
- Billing & Economic Layer
- Risk & Security Model

This document serves as the authoritative reference for:

- Engineering implementation
- Architecture audits
- Technical due diligence
- Strategic product alignment

---

# 1. System Definition

Krako 2.0 is a heterogeneous AI execution fabric that:

- Decomposes AI workloads into structured micro-tasks
- Executes structured computation across distributed CPU nodes
- Escalates irreducible generative tasks to centralized GPU-backed LLM Pods
- Minimizes large-model invocation while preserving correctness

Krako does NOT:

- Shard transformer layers across WAN
- Distribute KV cache
- Federate token-level generation
- Replace kernel-level inference engines

Core principle:

Deterministic Before Generative  
Distribute Structure, Not Tokens

---

# 2. Architectural Separation

Krako 2.0 is built on strict separation of concerns.

## 2.1 Control Plane – KORA

Responsibilities:

- Transform user request into TaskGraph (DAG)
- Decompose into WorkUnits
- Define escalation logic
- Attach constraints (latency, budget, privacy)
- Define idempotency and criticality

KORA decides WHAT should be executed.

KORA does NOT:
- Perform distributed scheduling
- Modify execution placement
- Handle retries
- Manage billing or reputation

---

## 2.2 Data Plane – Krako Fabric

Responsibilities:

- Validate TaskGraph schema
- Create ExecutionSession
- Enforce DAG dependencies
- Schedule WorkUnits
- Route LLM WorkUnits to Pods
- Enforce privacy constraints
- Emit execution telemetry

Krako decides WHERE and HOW to execute.

Krako does NOT:
- Change WorkUnit type
- Reinterpret escalation
- Override privacy rules
- Debit credits directly

---

## 2.3 Generative Core – LLM Pods

Responsibilities:

- Execute llm WorkUnits
- Maintain local KV cache
- Enforce tenant isolation
- Report token usage

LLM Pods are:

- GPU-backed
- Region-bound
- Session-isolated
- Memory-bound centralized executors

---

# 3. Execution Substrates

## 3.1 CPU Nodes

Execute:

- deterministic tasks
- retrieval tasks
- small_model tasks

Sources:

- Community contributors
- Datacenter CPU clusters
- Institutional machines

CPU nodes never execute large-model generative WorkUnits.

---

## 3.2 LLM Pods

Execute:

- llm WorkUnits only

Constraints:

- No cross-session KV reuse
- No WAN transformer sharding
- No shared tenant memory

---

# 4. Domain Integration

Core Aggregates:

- TaskGraph (Control Plane)
- ExecutionSession (Data Plane)
- WorkUnitExecution
- Node
- Pod
- Account / CreditWallet
- ReputationProfile

Each bounded context owns its invariants.

Billing and Trust consume execution events asynchronously.

Execution logic remains isolated from commercial logic.

---

# 5. End-to-End Execution Flow

1. Application submits request
2. KORA produces TaskGraph
3. TaskGraph submitted to Krako Gateway
4. ExecutionSession created
5. Scheduler resolves DAG dependencies
6. Eligible CPU WorkUnits dispatched
7. Eligible LLM WorkUnits routed to LLM Pod
8. Results aggregated deterministically
9. Telemetry events emitted
10. Billing & Trust contexts consume events

---

# 6. Escalation Model

Escalation is exclusively defined in Control Plane.

small → medium → large

Krako enforces escalation but never invents it.

No hidden automatic escalation.

Optional future: policy-driven downgrade if budget exceeded (explicit flag required).

---

# 7. Privacy & Isolation Model

Privacy is enforced at scheduling time.

WorkUnit.constraint.privacy:

- local_only → CPU Nodes within trust boundary only
- allow_remote → LLM Pod permitted

Scheduler invariant:

local_only must never be routed to LLM Pod.

LLM Pod invariant:

- Strict tenant isolation
- No cross-session KV cache reuse

---

# 8. Economic Model Integration

Billing is event-driven.

Billable sources:

- CPU execution duration
- LLM token usage
- Model tier

Execution layer emits usage.
Billing layer calculates cost.
Credits are debited asynchronously.

Scheduler never mutates CreditWallet.

---

# 9. Trust & Reputation Model

Trust context consumes:

- Success rate
- Failure rate
- Timeout frequency
- Retry amplification

Scheduler MAY weight placement using reputation.

Scheduler MUST NOT calculate reputation.

Trust and execution remain logically isolated.

---

# 10. Reliability & Safety Invariants

Hard invariants:

1. privacy=local_only never routed to LLM Pod
2. llm WorkUnit never executed on CPU node
3. Escalation never modified by Data Plane
4. No double billing on retry
5. DAG acyclicity always enforced
6. Required execution events always emitted

These invariants must be CI-gated.

---

# 11. Scaling Model

Krako scales by:

- Adding CPU nodes
- Adding regions
- Adding LLM Pods
- Queue partitioning
- Region-aware routing
- Admission control

Scheduler may shard queues per region or substrate.

---

# 12. Threat Model Summary

Primary P0 risks:

- Privacy leakage
- Result forgery
- Billing abuse

Mitigations:

- Hard placement rules
- Schema-verifiable outputs
- Budget enforcement pre-LLM
- Retry correlation safeguards

---

# 13. Strategic Positioning

Krako 2.0 is:

- Not a distributed transformer
- Not a GPU replacement
- Not a foundation model company

Krako 2.0 is:

An AI Execution Fabric that minimizes large-model invocation,
aggregates heterogeneous compute,
and enables hybrid local/remote execution.

---

# Change Log

## v1.0 (2026-02-25)
- Full detailed rewrite
- Integrated all subsystem specifications
- Expanded invariants and architectural separation
- Removed truncation issues
- Clarified escalation boundaries