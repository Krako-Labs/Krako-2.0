# Krako 2.0 – Telemetry & Event Specification (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the canonical telemetry and event model for Krako 2.0.

Telemetry is the integration backbone for:
- Observability
- Billing metering
- Trust/reputation scoring
- Debugging and replay

The execution layer emits events.
Billing and Trust consume events asynchronously.

This specification is implementation-oriented.

---

# 1. Principles

1. Event-driven execution accountability
2. At-least-once delivery
3. Idempotent consumption required
4. Execution does not mutate billing/trust directly
5. Minimal required event fields are mandatory

---

# 2. Canonical Event Envelope

All events MUST follow this envelope:

```json
{
  "event_id": "uuid",
  "event_type": "WorkUnitDispatched",
  "timestamp": "ISO8601",
  "tenant_id": "string",
  "graph_id": "uuid",
  "execution_session_id": "uuid",
  "work_unit_id": "uuid|null",
  "source": {
    "component": "scheduler | node_agent | llm_pod | gateway",
    "id": "string",
    "region": "string"
  },
  "payload": {}
}
```

Envelope invariants:
- event_id unique
- timestamp present
- tenant_id present
- graph_id and execution_session_id present

---

# 3. Execution Events (Scheduler)

## 3.1 ExecutionSessionStarted

```json
{ "status": "running" }
```

## 3.2 WorkUnitQueued

```json
{ "queue": "string" }
```

## 3.3 WorkUnitReady

```json
{ "dependencies_satisfied": true }
```

## 3.4 WorkUnitDispatched

```json
{
  "substrate": "cpu | llm_pod",
  "target_id": "node_id | pod_id",
  "region": "string"
}
```

## 3.5 WorkUnitStarted

```json
{ "started_at": "ISO8601" }
```

## 3.6 WorkUnitCompleted

```json
{
  "duration_ms": 320,
  "output_ref": "optional",
  "usage": {
    "tokens_in": 0,
    "tokens_out": 0,
    "cost_usd": 0.0
  }
}
```

## 3.7 WorkUnitFailed

```json
{
  "duration_ms": 120,
  "error": {
    "code": "TIMEOUT",
    "message": "string",
    "retryable": true,
    "details": {}
  }
}
```

## 3.8 WorkUnitRetried

```json
{
  "attempt": 2,
  "max_attempts": 3,
  "backoff_ms": 200
}
```

## 3.9 ExecutionSessionCompleted

```json
{
  "status": "success | failed | cancelled",
  "total_duration_ms": 1800,
  "total_usage": {
    "tokens_in": 1000,
    "tokens_out": 1200,
    "cost_usd": 0.05
  }
}
```

---

# 4. Node Events (Node Agent)

## 4.1 NodeRegistered

```json
{
  "node_id": "uuid",
  "agent_version": "1.0.0",
  "capabilities": { "cpu_cores": 16, "ram_mb": 32768 }
}
```

## 4.2 NodeHeartbeat

```json
{
  "cpu_load": 0.5,
  "available_ram_mb": 12000,
  "status": "healthy"
}
```

## 4.3 NodeUnavailable

```json
{ "reason": "heartbeat_timeout" }
```

---

# 5. LLM Pod Events

## 5.1 LLMInvocationStarted

```json
{
  "pod_id": "string",
  "tier": "small | medium | large",
  "model": "optional"
}
```

## 5.2 LLMInvocationCompleted

```json
{
  "pod_id": "string",
  "tier": "small | medium | large",
  "model": "optional",
  "duration_ms": 940,
  "tokens_in": 850,
  "tokens_out": 650,
  "total_tokens": 1500
}
```

## 5.3 LLMInvocationFailed

```json
{
  "pod_id": "string",
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "string",
    "retryable": true
  }
}
```

---

# 6. Billing Consumption

Billing Context consumes:
- WorkUnitCompleted
- LLMInvocationCompleted
- ExecutionSessionCompleted

Billing derives:
- billable tokens
- billable duration
- tier-based pricing

Billing must be idempotent and correlation-aware.

---

# 7. Trust Consumption

Trust Context consumes:
- WorkUnitCompleted
- WorkUnitFailed
- NodeUnavailable

Trust derives:
- reliability signals
- timeout rates
- failure rates

Trust updates must be asynchronous.

---

# 8. Delivery Guarantees

v1.0 guarantees:
- At-least-once delivery
- Best-effort ordering per execution_session_id

Consumers must deduplicate by event_id.

---

# 9. Retention & Replay

Minimum retention:
- Execution events for debugging

Production retention policy is environment-specific.

Replay is allowed only for:
- deterministic WorkUnits
- non-sensitive workloads

---

# 10. Hard Invariants

1. WorkUnitCompleted/Failed must include duration_ms.
2. LLMInvocationCompleted must include token metrics.
3. All events must include tenant_id and execution_session_id.
4. Event pipeline must support idempotent consumption.

---

# 11. Non-Goals

This specification does NOT:
- Prescribe monitoring UI
- Prescribe alerting thresholds
- Prescribe analytics stack

---

# Change Log

v1.0 – Full engineering rewrite replacing draft telemetry spec

