# Synaptic Mesh — Experiments (v1.4)

This directory contains the experimental framework for Synaptic Mesh v1.4.  
The goal is to evaluate stability, diversity, trust dynamics, and Sybil resistance under controlled conditions.

## Structure

- spec_v1.4.md — Full experiment specification  
- setup.md — Environment and reproducibility requirements  
- metrics.md — Definitions of all evaluation metrics  
- cases/ — Specific experiment scenarios (filled in v1.4 and v1.5)

## Purpose

The v1.4 experiments aim to answer:

1. Does local adaptation produce stable behavioral trajectories?
2. Under what conditions does diversity collapse?
3. How does trust converge under different feedback distributions?
4. What is the breakdown threshold for Sybil nodes?
5. Can useful behavior emerge without communication or shared memory?

These experiments are simulation-based and do not require inference engines or external models.
