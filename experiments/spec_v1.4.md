# Synaptic Mesh — Experiment Specification (v1.4)

## 1. Objective

Evaluate the evolutionary behavior of independent Mesh nodes under controlled feedback conditions.  
Focus areas:
- trust convergence
- diversity maintenance
- mutation stability
- Sybil resistance
- long-term drift behavior

---

## 2. Node Model

Each node consists of:
- Essence vector (n = 16)
- Trust scalar (0–1)
- Mutation operators (directional, exploratory, corrective, decay)
- Event-driven update loop

Nodes do not communicate and share no memory.

---

## 3. Experimental Variables

### 3.1 Node count
- 30
- 50
- 100

### 3.2 Sybil ratio
- 0.0
- 0.1
- 0.2
- 0.3

### 3.3 Feedback distribution
- uniform
- skewed_positive
- skewed_negative
- bursty
- adversarial

### 3.4 Mutation intensity
- low
- medium
- high

### 3.5 Initial Essence distribution
- random_normal
- clustered
- identical (collapse test)

---

## 4. Procedure

For each configuration:

1. Initialize N nodes with chosen Essence distribution  
2. Run 100–500 interaction steps per node  
3. At each step:  
   - sample feedback event  
   - update trust  
   - update Essence  
   - apply mutation if triggered  
4. Log all state transitions  
5. Compute metrics (see metrics.md)

---

## 5. Outputs

Each run produces:
- essence_drift.csv  
- trust_history.csv  
- mutation_events.csv  
- diversity_over_time.csv  
- sybil_impact.json  

These files are used for v1.5 reproducibility and analysis.

---

## 6. Success Criteria

A configuration is considered stable if:
- diversity > 0.4  
- trust_convergence < 0.6  
- mutation_rate does not diverge  
- no single node dominates (>40% trust share)  

A configuration is considered broken if:
- diversity < 0.2  
- trust collapses to 0 for >50% nodes  
- sybil nodes dominate trust ranking  
- mutation enters runaway regime

---

## 7. Notes

These experiments do not evaluate correctness or truth.  
They evaluate **evolutionary dynamics** under user-driven selection pressure.
