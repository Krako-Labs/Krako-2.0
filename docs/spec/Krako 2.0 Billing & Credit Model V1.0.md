# Krako 2.0 – Billing & Credit Model (Full Engineering Version)

Version: v1.0
Status: Engineering Specification
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 0. Purpose

This document defines the billing, credit, and metering model for Krako 2.0.

Billing is event-driven and consumes execution telemetry.

Goals:
- Define billing domain objects
- Define billable units for CPU and LLM execution
- Define credit wallet behavior
- Define idempotent charging rules
- Define retry and failure safety to prevent double billing

Non-goals:
- Payment processor integration
- Tax/VAT compliance
- Final pricing strategy

---

# 1. Principles

1. Execution emits usage; Billing computes cost.
2. Scheduler never debits credits.
3. Billing must be idempotent.
4. Retries must not double-bill.
5. Pod usage (tokens) is the source of truth for LLM charges.

---

# 2. Domain Objects

## 2.1 Account

Represents a billing tenant.

Fields:
- account_id
- tenant_id
- plan_id
- status (active/suspended)

---

## 2.2 CreditWallet

Represents prepaid value.

Fields:
- account_id
- balance_usd
- updated_at

Invariants:
- balance_usd >= 0 unless overdraft explicitly enabled

---

## 2.3 UsageRecord

Canonical record of billable usage.

Fields:
- usage_id
- execution_session_id
- work_unit_id
- substrate (cpu|llm_pod)
- billable_units
- cost_usd
- created_at

UsageRecord must be deduplicated and immutable once committed.

---

# 3. Billable Units

## 3.1 CPU WorkUnits

CPU cost is derived from measurable runtime signals.

Inputs:
- duration_ms
- resource_class (node class)

Baseline formula (conceptual):

cpu_cost_usd = duration_ms * cpu_rate_per_ms(resource_class)

Notes:
- Pricing can be tiered by stability_class (community vs datacenter).
- CPU pricing may include a minimum charge per WorkUnit.

---

## 3.2 LLM WorkUnits

LLM cost is derived from token metrics reported by LLM Pods.

Inputs:
- tokens_in
- tokens_out
- tier
- model (optional)

Baseline formula (conceptual):

llm_cost_usd = (tokens_in + tokens_out) * rate_per_token(tier)

Pods are the source of truth for token metrics.

---

# 4. Metering Flow

1. Execution emits events:
   - WorkUnitCompleted
   - LLMInvocationCompleted
   - ExecutionSessionCompleted

2. Billing consumes events.

3. Billing derives UsageRecord.

4. Billing debits CreditWallet.

5. Billing emits:
   - UsageRecorded
   - CreditsDebited

Execution remains correct even if Billing is temporarily unavailable.

---

# 5. Idempotency & Deduplication

Billing must deduplicate by stable keys.

Recommended dedup key:
- (tenant_id, execution_session_id, work_unit_id, attempt)

Rules:
- A WorkUnit attempt should be billed at most once.
- If multiple duplicate events arrive, only the first valid record is charged.

---

# 6. Retry Safety (No Double Billing)

If a WorkUnit is retried:

- Only successful attempt is billable
- Failed attempts may be optionally billable under policy (default: not billed)

For LLM invocations:
- If Pod reports token usage for a failed attempt, policy must define if it is billable.
- Default: bill only successful completions.

Scheduler must preserve correlation identifiers across retries.

---

# 7. Credit Enforcement

## 7.1 Pre-check Before LLM Invocation

Scheduler must enforce:
- available credit before dispatching llm WorkUnit

If insufficient:
- reject or terminate session with BUDGET_EXCEEDED

---

## 7.2 Post-charge

Billing updates CreditWallet:

balance_usd = balance_usd - cost_usd

If balance would go negative:
- reject charge
- mark account suspended (policy)

---

# 8. Pricing Plan Hooks (Interfaces)

Billing must support plan rules:

- per-tier rates
- per-node-class CPU rates
- min/max charge
- free tier caps

Pricing plan system is external but must be pluggable.

---

# 9. Revenue Share (Conceptual)

Billing may split cost allocation:

- Node payout portion
- Protocol fee portion
- Pod operator portion

Revenue share model is implementation-specific.

---

# 10. Auditability

Billing must provide:

- deterministic recomputation of charges from telemetry
- immutable UsageRecords
- credit ledger integrity

Audit trail must link:
- UsageRecord → event_id(s)

---

# 11. Hard Invariants

1. No direct credit debiting in execution layer.
2. Token metrics from Pod are source of truth.
3. Dedup key prevents double billing.
4. Retries preserve correlation IDs.
5. Credit pre-check must occur before llm dispatch.

---

# 12. Non-Goals

This spec does NOT:
- define payment provider APIs
- define refunds
- define tax/VAT handling

---

# Change Log

v1.0 – Full engineering rewrite replacing draft billing spec

