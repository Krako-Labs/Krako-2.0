# Krako 2.0 – Vision & Positioning

Version: v0.1
Status: Draft
Owner: Krako Core Team
Last Updated: 2026-02-25

---

# 1. Executive Summary

Krako 2.0 is a heterogeneous AI execution fabric designed to minimize large-model invocation by decomposing AI workloads into structured micro-tasks and executing them across distributed CPU resources before escalating to GPU-backed LLM Pods.

Krako does not attempt to shard transformer layers or distribute KV cache across nodes. Instead, it reduces the surface area where memory-bound large-model inference is required.

---

# 2. Vision

The long-term vision of Krako is to:

- Make AI infrastructure economically sustainable
- Reduce unnecessary dependency on large GPU clusters
- Enable local-first AI execution
- Provide hybrid scaling from local devices to regional LLM Pods
- Create a global heterogeneous AI execution network

Krako aims to become the execution layer between AI applications and large language models.

---

# 3. What Krako 2.0 Is

Krako 2.0 is:

- A distributed execution fabric
- A heterogeneous compute aggregator (CPU + GPU Pods)
- A micro-task scheduler
- A workload orchestration layer
- A hybrid local/remote AI execution platform

Krako executes structured, deterministic, retrieval, and small-model tasks across distributed nodes and routes irreducible generative tasks to regional LLM Pods.

---

# 4. What Krako 2.0 Is NOT

Krako 2.0 is NOT:

- A distributed transformer engine
- A KV cache federation system
- A GPU replacement system
- A foundation model company
- A transformer kernel optimization project

Krako does not distribute token-level generation across WAN-connected nodes.

---

# 5. Relationship with KORA

KORA is the execution intelligence layer (Control Plane).
Krako 2.0 is the distributed execution infrastructure (Data Plane).

KORA:
- Generates Task Graphs
- Determines escalation
- Enforces deterministic-first execution
- Controls token budgets

Krako:
- Executes Work Units
- Schedules across distributed CPU nodes
- Routes LLM tasks to Pods
- Aggregates results

KORA can run independently on a single machine.
Krako provides distributed scale.

---

# 6. Strategic Positioning

Krako sits between AI applications and large language models.

Traditional model:
Application → Direct LLM Call

Krako model:
Application → KORA → Krako Fabric → LLM Pod (only when required)

Krako reduces cost, improves margin, and enables hybrid scaling.

---

# 7. Target Users

- AI startups with high LLM cost
- Enterprise AI teams
- Developers using local LLMs
- Students and independent hackers (via KORA Studio)

---

# 8. Economic Thesis

Large language models are memory-bandwidth bound and GPU-dependent.
Most AI workloads contain structured components that do not require full large-model inference.

By resolving structured computation upstream, Krako reduces:

- LLM call frequency
- Token usage
- GPU dependency
- Infrastructure cost

---

# 9. Core Principles

1. Deterministic Before Generative
2. Escalate Only When Necessary
3. Keep Generation Centralized
4. Distribute Structure, Not Tokens
5. Separate Control Plane from Data Plane

---

# Change Log

## v0.1 (2026-02-25)
- Initial Vision & Positioning document created
