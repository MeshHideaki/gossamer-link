# v13.3.0 Trust Time

## Core
Introduced temporal decay to trust using last_active timestamps.

## Mechanism
Each node's influence is scaled by time_factor = exp(-(t - last_active) * decay).

## Structural Role
Suppresses inactive nodes and prioritizes recently active participants.

## Result
mean_variance within [0.02, 0.06] across all runs
trust spread ≥ 0.2
but trust saturation observed (most nodes ≈ 1.0)
structural collapse detected

## Conclusion
Temporal trust introduced, but causes saturation and ranking collapse.
