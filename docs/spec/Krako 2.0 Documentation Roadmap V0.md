# Krako 2.0 Documentation Roadmap

Version: v0.1
Status: Draft
Owner: Krako Core Team
Last Updated: 2026-02-25

---

## 📌 Versioning Policy

All Krako documentation follows semantic versioning:

- MAJOR: Structural or architectural change
- MINOR: New sections or expanded scope
- PATCH: Clarifications, wording fixes, non-structural edits

Each document must include:
- Version number (top of document)
- Last updated date
- Change log section (bottom of document)

---

# 📚 Master Documentation List

Below is the recommended order of creation.

---

# 1️⃣ Foundational Documents (Start Here)

## 1.1 Krako Vision & Positioning
Defines:
- What Krako 2.0 is
- What it is NOT
- Relationship between KORA and Krako
- Strategic positioning

Priority: HIGH

---

## 1.2 System Architecture Specification
Defines:
- Control Plane vs Data Plane
- Layer diagram
- Component responsibilities
- Non-goals (explicit exclusions)

Priority: HIGH

---

## 1.3 Domain Model (DDD Core)
Defines:
- Bounded contexts
- Aggregates
- Entities
- Value objects
- Ubiquitous language

Priority: HIGH

---

# 2️⃣ Data Plane Specifications (Krako 2.0 Core)

## 2.1 Task Graph Specification
- DAG structure
- Dependency rules
- Serialization format

## 2.2 Work Unit Specification
- JSON schema
- Constraints
- Execution hints
- Privacy flags

## 2.3 Scheduler Specification
- Placement policy
- Retry rules
- Timeout behavior
- Region handling

## 2.4 Node Agent Protocol
- Node registration
- Heartbeat
- Work pull/push
- Result reporting

## 2.5 Telemetry & Event Specification
- Execution events
- Token accounting
- Latency metrics
- Failure classification

---

# 3️⃣ LLM Pod Specification

## 3.1 LLM Pod Interface
- Input contract
- Output contract
- Token reporting

## 3.2 Model Tier Definitions
- Small
- Medium
- Large
- Capability boundaries

## 3.3 Privacy & Isolation Model
- Local-only execution
- Remote allowed execution
- Data boundary guarantees

---

# 4️⃣ Control Plane (KORA Integration)

## 4.1 KORA ↔ Krako Interface
- TaskGraph ingestion
- Escalation handling
- Budget propagation

## 4.2 Escalation Policy Spec
- Confidence thresholds
- Evidence rules
- Fallback behavior

---

# 5️⃣ Network & Trust Layer

## 5.1 Node Identity Model
- Node ID
- Region tagging
- Capability tagging

## 5.2 Reputation Model
- Success weighting
- Failure penalties
- Slashing rules

## 5.3 Security Model
- Signature validation
- Anti-replay
- Trust boundaries

---

# 6️⃣ Economic Model

## 6.1 Credit & Billing Model
- Token accounting
- Work unit cost mapping
- Remote escalation pricing

## 6.2 Revenue Share Model
- Node compensation
- LLM Pod compensation

---

# 7️⃣ KORA Studio Specification

## 7.1 Local Runtime Architecture
- Local model management
- Escalation trigger

## 7.2 Hybrid Execution Flow
- Local execution path
- Remote boost path

## 7.3 UX Flow
- Chat flow
- Boost notification
- Budget display

---

# 8️⃣ Operational Documents (Private)

## 8.1 Production Scheduler Design
## 8.2 Multi-Region Deployment
## 8.3 LLM Pod Infrastructure
## 8.4 Monitoring & SLO

---

# 🔄 Change Log

## v0.1 (2026-02-25)
- Initial documentation roadmap created
- Defined document ordering and priority
