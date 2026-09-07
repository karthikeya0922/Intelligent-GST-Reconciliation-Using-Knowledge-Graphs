# Temporal Graph Methodology & Leakage Prevention Architecture

## 1. The Threat of Graph Lookahead Bias
In static graph machine learning, graph features (such as PageRank, node embeddings, or neighbor aggregations) are computed over a single graph pooled across all available timestamps. In financial fraud and tax compliance forecasting, **this creates catastrophic data leakage**:

1. **Future Edge Leakage**: Invoices created in Month 20 form graph edges. If a static graph is evaluated at Month 2, the model observes high degree and connectivity that did not exist at Month 2.
2. **Future Topology Leakage**: An entity participating in a circular fraud ring in Month 18 would show non-zero cycle participation in Month 1, falsely teaching the model to detect future actions before they occur.
3. **Target Contagion Leakage**: Aggregating current-period neighbor labels ($T_{k+1}$) allows a model to "cheat" by reading the concurrent ground-truth status of connected peers.

---

## 2. Dynamic Temporal Snapshot Architecture
To guarantee scientific validity, our pipeline constructs time-parameterized graph snapshots $\mathcal{G}_{T_k}$ using `backend/ml/graph_features.py`:

```
All Historical Invoices (2024-05 to 2026-03)
                     │
                     ▼
       Temporal Filter: invoice_period <= T_k
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
Included in G(T_k)         Excluded from G(T_k)
(Edges <= T_k)             (Future Edges > T_k)
       │
       ▼
Extract Network Topologies at T_k:
- In/Out Degree Centrality
- PageRank
- Clustering Coefficient
- Reciprocal Trades
- Cycle Participation (L: 3-5)
       │
       ▼
Join with Historical Vendor States (t <= T_k):
- High-Risk Neighbor Count
- Neighbor Average Risk
```

---

## 3. Formal Invariants & Rules

### Rule 1: Monotonic Edge Ingestion
An edge $e = (u, v, t)$ is admitted into snapshot $\mathcal{G}_{T_k}$ if and only if:
$$\text{period}(t) \le T_k$$

### Rule 2: Lagged Neighbor State Alignment
Let $\mathcal{N}_{T_k}(v)$ be the set of adjacent nodes to vendor $v$ in snapshot $\mathcal{G}_{T_k}$. For any neighbor $u \in \mathcal{N}_{T_k}(v)$, the risk attribute assigned to $u$ must satisfy:
$$\text{State}(u) = \text{LatestAvailableRisk}(u, t \le T_k)$$
$$\text{State}(u) \neq \text{TargetRisk}(u, T_{k+1})$$

If neighbor $u$ has no prior recorded compliance history before or at $T_k$, its state is initialized to a documented neutral default ($0.0$).

---

## 4. Empirical Verification & Automated Leakage Audit

### 1. Automated Test Suite (`tests/ml/test_graph_temporal_leakage.py`)
Two explicit automated regression tests enforce this invariant in CI/CD:
1. `test_temporal_graph_leakage_invariance`: Asserts that modifying, injecting, or removing invoices in periods $T > T_k$ causes zero change in the feature vector computed at $T_k$.
2. `test_neighbor_risk_temporal_isolation`: Asserts that neighbor risk features cannot access $T_{k+1}$ or later labels.

### 2. Temporal Leakage Audit Report (`data/reports/ml/leakage_audit.json`)
The pre-training and post-graph audit inspected all 29 feature columns:
- **Total Features Audited**: 29
- **Passed Features**: 29
- **Failed Features**: 0
- **Future Dependency Detected**: False
- **Temporal Ordering Intact**: True
- **Overall Audit Status**: `PASSED`
