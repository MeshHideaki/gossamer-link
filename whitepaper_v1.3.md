# Synaptic Mesh v1.3 — Whitepaper  
**Author / Originator: Mesh Hideaki**

---

# 1. Introduction

Synaptic Mesh is an **Evolution OS**, not an AI model.  
It enables any small AI to evolve locally, without communication (v1.x),  
without centralized training, and without relying on large compute.

v1.3 represents the **design phase**:

- Philosophy  
- Mathematical specification  
- Architecture  
- Initial simulation observations  
- Failure scenarios  
- Minimal experiment plan  
- Limitations and non-goals  

v1.4 will introduce **experiments**, including:

- Sensitivity analysis  
- Breakdown scenarios  
- Reproducibility  

---

# 2. Philosophy

## 2.1 Mesh is not an AI — it is an OS
- AI = inference  
- Mesh = evolution  

Mesh does not answer.  
Mesh grows.

---

## 2.2 No inference
Mesh performs:

- State updates  
- Trust updates  
- Mutation selection  
- Evolution loop management  

Mesh does **not** perform reasoning.

---

## 2.3 v1.x = local only / v2.x = optional networking
- v1.x: fully local, no communication  
- v2.x: optional networking (libp2p / WebRTC)

---

## 2.4 User reactions drive evolution
User events:

- COPY → useful  
- SKIP → not useful  
- REVISE → needs improvement  
- DWELL_TIME → interest  

Mesh optimizes **usefulness**, not truth.

---

## 2.5 Diversity is preserved
Mesh avoids collapse by:

- Controlled mutation  
- Trust-based suppression of malicious nodes  
- Normalized Essence vectors  
- Subjective layers  

---

## 2.6 Direction alignment (hypothesis)

Direction alignment **may emerge** under shared user feedback conditions.  
This is a **hypothesis**, not a proven mechanism, and will be tested in v1.4.

---

# 3. Purpose

Mesh aims to:

- Democratize AI evolution  
- Enable fully local growth  
- Preserve diversity  
- Handle subjective knowledge  
- Coexist with large models (“external brains”)  

---

# 4. Components

- **Essence** (16‑dim vector)  
- **Trust** (0–1 scalar)  
- **Mutation operators**  
- **Evolution loop**  

---

# 5. Usage

Requirements:

- A node (AI)  
- User reactions  
- Local storage  

Mesh does not perform inference.

---

# 6. Capabilities

- Local evolution  
- Diversity maintenance  
- Sybil resistance  
- Subjective knowledge handling  
- External brain integration  

---

# 7. Limitations

- No inference  
- No communication (v1.x)  
- No truth evaluation  
- No centralized control  
- Essence is not a universal representation  

---

# 8. Math Specification

### Essence normalization  
`v = v / ||v||`

### Trust update  
`Δtrust = 0.06 * improvement + 0.03 * (agg_score - 0.5) - decay(node_type)`  
`trust_new = clip(trust_old + Δtrust, 0, 1)`

### Improvement score  
`score = 0.6 * coherence + 0.4 * novelty - penalty`

### Novelty  
`||new_vec - old_vec|| / 2`

### Sybil cluster detection  
`avg_sim > 0.85 → sybil cluster`

---

# 9. Initial Observations (Not Proof)

Simulation (50 nodes × 100 rounds):

sybil_resistance      0.9999  
knowledge_survival    1.0000  
evolution_quality     0.4558  
diversity_maintenance 0.6906  
trust_convergence     0.3120  

These are **observations**, not proofs.  
They depend on parameters and initial conditions.

---

# 9.5 Expected Failure Scenarios

Synaptic Mesh may break under:

- Highly biased user feedback distributions  
- Extreme Sybil cluster density (>30%)  
- Low-diversity mutation regimes  
- Overdominant trust convergence  

---

# 9.6 Minimal Experiment Plan (v1.4)

### Node Counts
- 30 / 50 / 100

### Sybil Ratios
- 0.1 / 0.2 / 0.3

### Feedback Distributions
- Uniform  
- Skewed  

### Metrics
- Trust convergence  
- Diversity  
- Sybil impact  
- Evolution quality  

### Goal  
→ Identify **breakdown thresholds**.

---

# 10. Future Work

- v2.x networking  
- Signature layer  
- Distributed logs  
- Mesh-native apps  

---

# 11. Non-Goals

- Not a general AI  
- Not a reasoning engine  
- Not a centralized network  

---

# 12. Glossary

- Essence  
- Trust  
- Mutation  
- UserEvent  
- Sybil node  
