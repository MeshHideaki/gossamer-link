# Simulation (v1.5)

This directory contains the executable simulation for Synaptic Mesh experiments.

## Update (v1.5)
Feedback is now behavior-based:
- High-trust nodes receive positive feedback
- Low-trust nodes receive negative/neutral feedback
- Mid-trust nodes receive stochastic feedback

This creates more realistic adaptation dynamics.

## Files
- run.py — Main simulation loop (v1.5)
- config.json — Parameters for mutation, trust, and feedback
- README.md — This file

## Output
The simulation produces:
- essence_drift.csv
- trust_history.csv
- mutation_events.csv
- diversity_over_time.csv
- sybil_impact.json
