# Krako 2.0 – Risk & Attack Scenarios Review

Version: v0.1
Status: Draft
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document reviews key failure modes, adversarial scenarios, and operational risks for Krako 2.0 based on the current spec set.

Scope:
- Technical failures (reliability, correctness)
- Security & adversarial nodes
- Privacy & data boundary risks
- Billing fraud and abuse
- LLM Pod operational risks

Non-goals:
- Full cryptographic design
- Full compliance/legal policy

---

# 1. System Threat Surface (High-Level)

Krako 2.0 threat surface includes:

- Public ingress (TaskGraph submission)
- Scheduler (placement + execution control)
- Node Agent runtime on heterogeneous nodes
- LLM Pod endpoints
- Event pipeline (telemetry/metering)
- Billing/credits

---

# 2. Priority Risk Register (P0–P2)

Legend:
- P0: existential / catastrophic
- P1: major incident / large financial or privacy impact
- P2: moderate impact

---

## 2.1 P0 – Privacy Boundary Violation (local_only leakage)

Scenario:
- A WorkUnit marked privacy=local_only is routed to an untrusted node or LLM Pod.

Impact:
- Data exposure, irreversible trust loss.

Likely causes:
- Scheduler bug
- Mis-tagged nodes (trust boundary confusion)

Mitigations:
- Scheduler hard-gate: local_only → allowlist of Trusted Nodes only
- Unit/integration tests: “privacy invariant tests” on every change
- Audit log: every placement decision with privacy flag

Spec hardening needed:
- Add explicit “trusted_node_required=true” field derivation in WorkUnit constraints (v0.2)

---

## 2.2 P0 – Result Integrity Failure (malicious node returns forged outputs)

Scenario:
- Node Agent returns plausible but incorrect/malicious output.

Impact:
- Silent corruption, customer harm.

Mitigations:
- Deterministic tasks must be verifiable (schema + checksums)
- Quorum execution for high-risk WorkUnits (optional policy)
- Spot-check / canary tasks
- Signed results + replay protection (private)

Spec hardening needed:
- Add “verification_mode” to WorkUnit (none|schema|quorum|recompute) (v0.2)

---

## 2.3 P0 – Billing Fraud / Credit Drain

Scenario:
- Attacker triggers repeated LLM Pod calls (expensive) via prompt injection or API abuse.

Impact:
- Direct cost explosion.

Mitigations:
- Admission control on tenant budgets
- Per-tenant rate limits
- Budget caps enforced before LLM invocation
- Detect retry loops (idempotency + correlation IDs)

Spec hardening needed:
- Add “max_llm_invocations_per_session” at graph-level policy (v0.2)

---

## 2.4 P1 – LLM Pod Tenant Isolation Failure

Scenario:
- Misconfiguration or caching leaks cross-tenant context.

Impact:
- Severe privacy breach.

Mitigations:
- Explicit isolation rules (already documented)
- Disable prompt logging by default
- Strong separation of session identifiers
- Regional compliance profiles

Spec hardening needed:
- Add “logging_mode” policy (off|minimal|debug) (v0.2)

---

## 2.5 P1 – Prompt Injection / Tool Abuse in Retrieval Pipeline

Scenario:
- Retrieved documents contain malicious instructions that cause escalation or data exfiltration.

Impact:
- Undesired LLM calls, leakage, harmful tool actions.

Mitigations:
- Treat retrieval outputs as untrusted data
- Strict tool permissioning and schema validation
- Separate “instructions” vs “evidence” channels in context_pack
- KORA should perform injection-resistant context packing

Spec hardening needed:
- Define “context_pack schema” and channel separation (v0.2)

---

## 2.6 P1 – Scheduler Hotspot / Global Throughput Collapse

Scenario:
- Scheduler bottleneck under load; queue buildup; cascading retries.

Impact:
- Elevated latency, widespread failures.

Mitigations:
- Queue partitioning
- Backpressure and admission control
- Circuit breakers per region
- Limit retries under congestion

Spec hardening needed:
- Add congestion signals into telemetry (v0.2)

---

## 2.7 P2 – Node Churn & Partial Availability

Scenario:
- Community nodes drop frequently; execution becomes unstable.

Impact:
- Increased retries, latency.

Mitigations:
- Prefer stable nodes for critical tasks
- Session pinning to stable pools
- SLA tiers (datacenter nodes vs community)

Spec hardening needed:
- Add “stability_class” tag for nodes (v0.2)

---

# 3. Attack Scenarios by Component

## 3.1 Gateway / Submission

- API abuse (high QPS)
- Malformed graphs
- Graph bombs (huge DAG)

Controls:
- Schema validation
- Max graph size limits
- Tenant quotas

---

## 3.2 Scheduler

- Placement manipulation attempts
- Retry amplification

Controls:
- Deterministic placement invariants
- Retry budgets
- Audit logs

---

## 3.3 Node Agents

- Malicious runtime / tampered agent
- Exfiltration attempts

Controls:
- Sandboxing
- Disable outbound network unless needed
- Signed results (private)

---

## 3.4 LLM Pods

- Isolation misconfig
- Cost runaway

Controls:
- Strict session isolation
- Budget checks pre-invocation
- Rate limits

---

## 3.5 Telemetry Pipeline

- Event spoofing
- Partial loss

Controls:
- At-least-once delivery
- Idempotent consumers
- Signed events (private)

---

# 4. Required “Invariant Tests” (Minimum Suite)

These tests should gate merges:

1) Privacy invariant: local_only never routed to Pod
2) Substrate invariant: llm WorkUnit never routed to CPU node
3) Idempotency invariant: retries never double-bill
4) DAG invariant: no cycles, dependencies satisfied
5) Event invariant: WorkUnitCompleted always emitted with required fields

---

# 5. Spec Update Recommendations

Propose the following v0.2 upgrades:

- WorkUnit: verification_mode, trusted_node_required
- TaskGraph: max_llm_invocations_per_session, max_graph_size
- Telemetry: congestion + retry amplification signals
- LLM Pod: logging_mode policy
- Context Pack: explicit schema with channel separation

---

# Change Log

## v0.1 (2026-02-25)
- Initial risk and attack scenario review created
- Defined P0–P2 risks, mitigations, and recommended spec hardening actions

