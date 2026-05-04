# v12.3.0 Failure Analysis

## Issue
mean_variance is below required range in all runs.

## Cause
Winner-take-all extraction collapses diversity.

## Attempt
Selected highest novelty * trust vector per slot.

## Next Action
Introduce partial aggregation instead of single selection.
