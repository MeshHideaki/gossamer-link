# v11.3.0 Search

## Summary
Search upgraded to combine top-K selection with diversity constraint.

## Mechanism
- Global scoring (trust + similarity)
- Diversity filter (similarity < 0.8 between selected nodes)
- Random fallback to fill K

## Result
- Variance maintained (~0.0316)
- Trust distribution widened
- No structural collapse

## Conclusion
Search improves exploration without destabilizing the system.
