# v12.1.0 Query-Driven Propagation

## Core
Replaced passive neighbor-based propagation with active query-driven interaction.

## Mechanism
- QUERY_K = 2
- Nodes actively select targets based on:
  - trust (0.5)
  - novelty = 1 - similarity (0.5)

## Structural Role
- Promotes information gain over redundancy
- Encourages diversity across nodes
- Reduces local convergence bias

## Result
- mean_variance within [0.02, 0.06] across all runs
- trust spread consistently above 0.2
- no structural collapse observed

## Validation
All three runs satisfied evaluation criteria:
- mean_variance ∈ [0.02, 0.06]
- max(trust) - min(trust) ≥ 0.2
- stable structure maintained

## Conclusion
Query-driven propagation improves exploration efficiency while preserving structural stability and diversity.
