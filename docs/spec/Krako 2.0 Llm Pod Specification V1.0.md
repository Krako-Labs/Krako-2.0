# Krako 2.0 – LLM Pod Specification (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

Source Reference: fileciteturn6file0

---

# 0. Purpose

This document defines the complete production-level specification of LLM Pods within Krako 2.0.

LLM Pods are centralized, GPU-backed execution endpoints responsible for memory-bandwidth-bound generative inference.

This specification replaces draft versions and clarifies:

- Execution contract
- Tier semantics
- Isolation guarantees
- Capacity and scaling model
- Billing interaction
- Failure handling
- Invariants

---

# 1. Architectural Role

LLM Pods belong to the Generative Core layer.

Responsibilities:
- Execute llm WorkUnits
- Maintain session-local KV cache
- Enforce strict tenant isolation
- Report structured usage metrics

LLM Pods do NOT:
- Execute deterministic/retrieval/small_model tasks
- Participate in WAN-level KV distribution
- Perform scheduling decisions
- Modify escalation intent

---

# 2. Execution Contract

## 2.1 Invocation Request

Scheduler → LLM Pod

```json
{
  "work_unit_id": "uuid",
  "graph_id": "uuid",
  "execution_session_id": "uuid",
  "tier": "large",
  "model": "optional",
  "input": {
    "prompt": "string",
    "context_pack": {},
    "system_prompt": "string"
  },
  "constraints": {
    "max_tokens": 2000,
    "temperature": 0.2,
    "top_p": 0.95,
    "timeout_ms": 8000
  },
  "metadata": {
    "tenant_id": "string",
    "region": "eu-west"
  }
}
```

Rules:
- `tier` defines required capability class.
- `model` is optional override within tier.
- Pod must validate tier compatibility.
- Pod must reject requests exceeding declared limits.

---

## 2.2 Invocation Response

Success:

```json
{
  "work_unit_id": "uuid",
  "status": "success",
  "output": {
    "text": "generated text",
    "structured": null
  },
  "usage": {
    "tokens_in": 850,
    "tokens_out": 650,
    "total_tokens": 1500
  },
  "duration_ms": 940
}
```

Failure:

```json
{
  "work_unit_id": "uuid",
  "status": "failed",
  "error": {
    "code": "TIMEOUT",
    "message": "string",
    "retryable": true
  }
}
```

Pods must never partially return output.

---

# 3. Model Tier System

Tiers are capability abstractions.

## 3.1 small
- May run locally or in cost-optimized Pods
- Short context
- Low reasoning depth

## 3.2 medium
- GPU-backed
- Moderate context
- Balanced cost

## 3.3 large
- GPU-backed
- High reasoning capability
- Extended context

Scheduler must not auto-upgrade tier without explicit policy flag.

---

# 4. Isolation & Privacy Model

## 4.1 Session Isolation

- KV cache isolated per session
- No cross-session KV reuse
- No shared prompt state

## 4.2 Tenant Isolation

- Strict tenant_id scoping
- No shared mutable memory across tenants

## 4.3 Privacy Enforcement

If WorkUnit.constraint.privacy = local_only:
- Scheduler must block routing

LLM Pod must never override privacy decision.

---

# 5. Regional Model

Each Pod is bound to:
- region_id
- compliance_profile

Example:

```json
{
  "region": "eu-west",
  "compliance_profile": ["gdpr"]
}
```

Scheduler must enforce regional constraints.

---

# 6. Capacity Model

Pods expose:

```json
{
  "pod_id": "pod-1",
  "region": "eu-west",
  "model_tiers": ["medium", "large"],
  "max_concurrent_requests": 128,
  "status": "healthy"
}
```

Capacity controls:
- Hard concurrency cap
- Admission rejection when saturated
- Region-level load balancing

Autoscaling implementation remains private.

---

# 7. Retry & Idempotency

LLM WorkUnits may be retried only if:
- idempotent = true
- retryable error

Retries must:
- Preserve correlation id
- Avoid duplicate billing
- Avoid duplicate side effects

---

# 8. Billing Interaction

LLM Pods report:
- tokens_in
- tokens_out
- total_tokens
- duration_ms

Billing layer consumes events.
Pods do NOT modify credit state.

---

# 9. Observability

Pods must emit:
- InvocationStarted
- InvocationCompleted
- InvocationFailed

Events must include:
- work_unit_id
- execution_session_id
- region
- token usage
- duration

Event delivery must be at-least-once.

---

# 10. Failure Handling

Common failure codes:
- TIMEOUT
- RESOURCE_EXHAUSTED
- MODEL_UNAVAILABLE
- RATE_LIMITED

Scheduler decides retry or fail.
Pods must remain stateless across failures.

---

# 11. Hard Invariants

1. No WAN KV federation
2. No cross-session KV reuse
3. No WorkUnit type modification
4. No privacy override
5. No duplicate billing on retry

These invariants must be enforced via integration tests.

---

# 12. Non-Goals

This specification does NOT define:
- Transformer implementation
- Kernel-level optimization
- Model training
- Distributed attention

LLM Pods are centralized execution units only.

---

# Change Log

v1.0 – Full engineering rewrite replacing draft v0.2

