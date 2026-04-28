# Synaptic Mesh — Metrics (v1.4)

## 1. Diversity

Measures behavioral spread across Essence vectors.

diversity = average_pairwise_distance(E)

Range: 0 (collapse) to 1 (max spread)

---

## 2. Trust Convergence

Measures how quickly trust values stabilize.

trust_convergence = variance(trust_t) over last 20% of steps

Lower is more stable.

---

## 3. Sybil Impact

Measures how much Sybil nodes distort trust ranking.

sybil_impact = trust_share(sybil_nodes)

Thresholds:
- <0.2 = safe  
- 0.2–0.4 = degraded  
- >0.4 = compromised  

---

## 4. Evolution Quality

Measures improvement in behavioral coherence and novelty.

evolution_quality = 0.6·coherence + 0.4·novelty

---

## 5. Mutation Stability

mutation_stability = 1 - variance(mutation_strength)

High variance indicates instability.

---

## 6. Drift Magnitude

drift = ||E_final - E_initial||

Used to detect runaway evolution.

---

## 7. Collapse Indicator

collapse = 1 if diversity < 0.2 else 0
