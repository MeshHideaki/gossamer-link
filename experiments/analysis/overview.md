# Analysis Overview (v1.4)

This directory contains analysis scripts for evaluating experiment outputs.

## Files
- diversity_analysis.py — Computes diversity metrics and collapse detection
- trust_analysis.py — Computes trust convergence and freeze detection
- mutation_analysis.py — Evaluates mutation stability and runaway behavior

## Input Files
- essence_drift.csv
- trust_history.csv
- mutation_events.csv
- diversity_over_time.csv
- sybil_impact.json

## Output
Each script produces:
- summary.json
- plots/ (optional, v1.5)
