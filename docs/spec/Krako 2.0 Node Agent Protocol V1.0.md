# Krako 2.0 – Node Agent Protocol (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the complete runtime and protocol specification for CPU-based Node Agents participating in the Krako 2.0 network.

The Node Agent is the execution runtime for CPU substrates.

It is responsible for:
- Node identity registration
- Capability reporting
- Heartbeat signaling
- Secure WorkUnit execution
- Result reporting
- Resource enforcement

This document replaces draft versions.

---

# 1. Node Agent Role

Node Agents execute WorkUnits of type:
- deterministic
- retrieval
- small_model

Node Agents MUST NOT:
- Execute llm WorkUnits
- Modify WorkUnit payloads
- Escalate tasks independently
- Perform billing logic

Node Agents operate under Scheduler authority.

---

# 2. Node Identity Model

Each Node Agent must maintain a stable identity.

## 2.1 Required Identity Fields

- node_id (UUID)
- public_key (for result signature verification)
- region
- agent_version
- capability_profile

node_id must remain stable across restarts.

---

# 3. Capability Profile

Node capability structure:

```json
{
  "cpu_cores": 16,
  "ram_mb": 32768,
  "arch": "x86_64",
  "instruction_sets": ["avx2"],
  "accelerators": [],
  "stability_class": "community | datacenter"
}
```

Capabilities must be declared at registration.

Scheduler uses capabilities for placement filtering.

---

# 4. Registration Protocol

## 4.1 Registration Request

Node → Scheduler

```json
{
  "node_id": "uuid",
  "public_key": "string",
  "region": "eu-west",
  "capabilities": { ... },
  "agent_version": "1.0.0"
}
```

## 4.2 Registration Response

Scheduler → Node

```json
{
  "status": "accepted",
  "heartbeat_interval_ms": 5000
}
```

Possible statuses:
- accepted
- rejected
- quarantined

---

# 5. Heartbeat Protocol

Node Agents must send periodic heartbeats.

## 5.1 Heartbeat Request

```json
{
  "node_id": "uuid",
  "timestamp": "ISO8601",
  "health": {
    "cpu_load": 0.42,
    "available_ram_mb": 24000,
    "status": "healthy"
  }
}
```

If heartbeats are missed beyond threshold:
- Node is marked unavailable
- In-flight WorkUnits may be retried elsewhere

---

# 6. WorkUnit Dispatch Model

v1.0 uses pull-based execution.

## 6.1 Pull Request

Node → Scheduler

```json
{
  "node_id": "uuid",
  "max_concurrent": 2
}
```

## 6.2 Dispatch Response

```json
{
  "work_units": [ { ...WorkUnit... } ]
}
```

Node Agents control local concurrency.

---

# 7. Execution Rules

Upon receiving a WorkUnit, Node Agent must:

1. Validate WorkUnit schema
2. Verify capability requirements
3. Enforce resource limits
4. Execute within sandbox
5. Respect timeouts
6. Produce structured WorkUnitResult

Execution must be isolated.

---

# 8. Sandboxing Requirements

Node Agents must:

- Restrict memory to declared limits
- Restrict CPU usage within allocation
- Prevent arbitrary outbound network calls unless explicitly allowed
- Isolate filesystem access

Sandbox implementation is environment-specific but mandatory.

---

# 9. WorkUnitResult Reporting

Node → Scheduler

```json
{
  "work_unit_id": "uuid",
  "status": "success | failed | timeout",
  "started_at": "timestamp",
  "finished_at": "timestamp",
  "duration_ms": 123,
  "output": {},
  "usage": {
    "tokens_in": 0,
    "tokens_out": 0
  },
  "execution": {
    "node_id": "uuid",
    "region": "eu-west"
  },
  "error": null
}
```

Results must be signed in production (private implementation).

---

# 10. Failure Handling

Failure types:
- EXECUTION_ERROR
- TIMEOUT
- RESOURCE_EXHAUSTED

If Node crashes mid-execution:
- Scheduler detects via timeout
- WorkUnit retried if idempotent

Repeated failures may trigger quarantine (Trust Context).

---

# 11. Concurrency Model

Node Agent must:
- Respect max_concurrent
- Avoid duplicate execution
- Maintain local execution queue

No WorkUnit may run twice simultaneously.

---

# 12. Security Requirements

Minimum:
- TLS communication
- Node identity verification
- WorkUnitResult integrity verification

Advanced (private layer):
- Result signature validation
- Attestation
- Anti-replay mechanisms

---

# 13. Hard Invariants

1. llm WorkUnits never executed
2. WorkUnit schema must validate before execution
3. No outbound network unless explicitly allowed
4. Execution resource limits enforced
5. No duplicate WorkUnit execution

---

# 14. Non-Goals

Node Agent does NOT:
- Perform scheduling
- Modify WorkUnits
- Compute reputation scores
- Debit credits

---

# Change Log

v1.0 – Full engineering rewrite replacing draft Node Agent specification

