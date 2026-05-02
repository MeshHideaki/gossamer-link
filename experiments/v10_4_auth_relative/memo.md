# v10.4.1 — Auth Relative Stabilization

Purpose:
Fix trust saturation by introducing relative normalization.

Setup:
Nodes=10, Steps=400, SEARCH_K=5

Result:
Trust no longer saturates.
Variance increased (~0.046).
System maintains differentiation.

Conclusion:
Relative normalization stabilizes trust dynamics.

--- JP ---
相対評価で信頼飽和を防止
分散が回復（約0.046）
ノード間の差が維持
安定動作を確認
