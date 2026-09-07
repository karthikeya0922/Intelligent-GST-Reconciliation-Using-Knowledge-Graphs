# Phase 2.1: Graph Neural Network (GNN) Gate Evaluation

## Final Recommendation: **NOT JUSTIFIED**
### Decision: `DO NOT FORCE GNN`

> [!IMPORTANT]
> The controlled 5-seed evaluation demonstrates that graph features provide neutral incremental predictive value (Macro F1 delta: -0.0004 across 5 seeds: 0.7404 Tabular vs 0.7400 Graph-Enhanced). Graph features account for only 0.02% of Tree SHAP attribution due to severe network sparsity (>99.6% zero values in graph metrics). Therefore, deploying a deep Graph Neural Network (GNN/GraphSAGE) is completely unjustified and would introduce substantial architectural complexity, GPU dependencies, and inference latency without measurable predictive benefit.

## 10-Criteria Formal Evaluation

| # | Evaluation Criterion | Empirical Finding & Evidence | Status |
|:---:|:---|:---|:---:|
| 1 | **Graph Predictive Improvement** | Macro F1 Delta: -0.0004 (Relative: -0.05%), High-Risk Recall Delta: -0.0046 | `FAIL` |
| 2 | **Number of Nodes** | 2,015 distinct GST taxpayers in benchmark universe | `PASS (ADEQUATE)` |
| 3 | **Number of Edges** | 168,213 chronological B2B invoice edges over 24 months | `PASS (ADEQUATE)` |
| 4 | **Edge-Type Diversity** | Primarily homogeneous B2B commercial invoice transactions and statutory GSTR return links | `NEUTRAL` |
| 5 | **Temporal Graph Snapshots** | Strict dynamic time-windowing G(T_k) required monthly to prevent leakage; full dynamic GNN adds high temporal maintenance complexity | `NEUTRAL/CONCERN` |
| 6 | **Graph Connectivity** | Zero-degree vendors in network: 99.65%. Modest density with core hubs and sparse periphery | `NEUTRAL` |
| 7 | **Number of Labeled Nodes** | 46,345 vendor-period ground-truth risk observation instances across 24 periods | `PASS (SUFFICIENT)` |
| 8 | **Graph Feature Importance** | Graph features represent 0.02% of total Tree SHAP attribution (0 features in Top 10, 1 in Top 20) | `FAIL (NEGLIGIBLE ATTRIBUTION)` |
| 9 | **Computational Feasibility** | Tabular+Graph XGBoost runs in <15ms inference on CPU. GNN requires PyTorch Geometric/DGL, GPU infrastructure, and sub-graph neighborhood sampling latency | `FAIL (DISADVANTAGE FOR GNN)` |
| 10 | **Incremental Information Beyond Tabular** | Tabular compliance and reconciliation features explain >99.9% of SHAP attribution. Graph metrics are heavily zero-inflated (>99.6% zeros) | `FAIL (REDUNDANT/SPARSE)` |
