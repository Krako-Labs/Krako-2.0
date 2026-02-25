# Krako 2.0 – Node Identity & Trust Model (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the identity, trust, and reputation model for CPU Nodes in Krako 2.0.

Trust is logically separated from execution. The Scheduler consumes trust signals but does not compute them.

Goals:
- Define Node identity lifecycle
- Define trust boundaries
- Define reputation scoring inputs
- Define slashing and quarantine behavior
- Define separation between Execution and Trust contexts

Non-goals:
- Define proprietary reputation formula
- Define specific cryptographic attestation implementation

---

# 1. Node Identity

## 1.1 Identity Requirements

Each Node Agent must maintain:

- node_id (UUID)
- public_key (for result integrity validation)
- region
- agent_version
- capability_profile

node_id must be stable across restarts unless explicitly revoked.

---

## 1.2 Registration States

Node lifecycle states:

- unregistered
- registered
- active
- quarantined
- suspended
- removed

State transitions:

- Registration accepted → active
- Suspicious behavior → quarantined
- Repeated violations → suspended or removed

---

# 2. Trust Zones

Krako defines logical trust boundaries.

## 2.1 Trusted Nodes

Examples:
- Datacenter-controlled nodes
- Enterprise-controlled infrastructure

May execute:
- privacy=local_only
- deterministic
- retrieval
- small_model

---

## 2.2 Semi-Trusted Nodes

Examples:
- Community contributors

May execute:
- deterministic
- retrieval (policy-dependent)

Never allowed:
- privacy-sensitive workloads

Trust zone classification must be configurable.

---

# 3. Reputation Model

Reputation is computed asynchronously from telemetry.

## 3.1 Reputation Signals

Derived metrics:

- Success rate
- Failure rate
- Timeout frequency
- Retry amplification
- Latency deviation from baseline
- Schema verification failures

---

## 3.2 Reputation Profile

Canonical structure:

```json
{
  "node_id": "uuid",
  "score": 0.87,
  "stability_class": "community | datacenter",
  "last_updated": "timestamp"
}
```

Score range:
- 0.0 = untrusted
- 1.0 = highly reliable

---

# 4. Reputation Effects

Scheduler MAY use reputation score to:

- Weight placement scoring
- Limit concurrency
- Restrict high-risk WorkUnits
- Prefer stable nodes for critical tasks

Scheduler MUST NOT:
- Modify reputation directly

---

# 5. Quarantine & Slashing

Triggers:

- Repeated invalid outputs
- Manipulated results
- Replay attacks
- Persistent timeouts
- Verification_mode failures

Actions:

- Reputation downgrade
- Temporary quarantine
- Concurrency cap
- Permanent removal

Exact thresholds are implementation-specific.

---

# 6. Result Integrity Requirements

Minimum production safeguards:

- WorkUnitResult must include node_id
- Results must be signed (private implementation)
- Replay protection required

Optional advanced controls:

- TEE attestation
- Remote proof of execution
- Quorum verification for high-risk tasks

---

# 7. Trust Context Isolation

Trust system must:

- Consume events asynchronously
- Never block execution pipeline
- Publish NodeTrustUpdated events

Execution must continue even if Trust system is degraded.

---

# 8. Stability Classes

Nodes may be tagged as:

- community
- datacenter
- enterprise

Stability class may influence:

- Pricing rates
- Placement weighting
- Workload eligibility

---

# 9. Hard Invariants

1. Trust logic must not execute inside Scheduler core.
2. Reputation updates must be event-driven.
3. Execution correctness must not depend on trust availability.
4. No WorkUnit may execute on suspended nodes.

---

# 10. Non-Goals

This specification does NOT:

- Define cryptographic protocol details
- Define exact scoring formula
- Define economic incentive structure

---

# Change Log

v1.0 – Full engineering rewrite replacing draft trust model

