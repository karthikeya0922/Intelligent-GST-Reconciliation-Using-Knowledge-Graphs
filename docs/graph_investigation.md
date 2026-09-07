# Knowledge Graph Investigation Layer

## 1. Role in the Production Risk Engine
Phase 2.1 demonstrated that Knowledge Graph features provide neutral incremental value when used directly in tree-based risk prediction ($0.7404$ Tabular vs $0.7400$ Graph-Enhanced Macro F1, $p = 0.8125$). However, the Knowledge Graph remains an indispensable **investigative and network context layer**:

```text
Prediction Layer:       Tabular XGBoost (Scores risk, calculates probabilities)
                              │
Investigation Layer:    Knowledge Graph (Explores counterparties, explains ties)
```

The Knowledge Graph answers questions that tabular features cannot address:
- *Who are this vendor's primary upstream suppliers and downstream buyers?*
- *Is there evidence of artificial volume passing (reciprocal trade loops)?*
- *Is the vendor participating in a multi-hop circular invoicing syndicate?*
- *Is there high commercial concentration (>80% of volume) with a single counterparty?*

---

## 2. Temporal Snapshot Invariants
To ensure regulatory audit defensibility, graph queries never query an all-time static graph. For any assessment at period $T_k$, the graph investigator constructs a snapshot graph $\mathcal{G}(t \le T_k)$:

$$\mathcal{G}_{T_k} = (\mathcal{V}_{T_k}, \mathcal{E}_{T_k}), \quad \mathcal{E}_{T_k} = \{e = (u, v, t) \mid t \le T_k\}$$

Any invoice or trade relationship established after $T_k$ is strictly omitted.

---

## 3. Structural Investigation Capabilities

### 1. Direct Counterparty Topology
- `supplier_count`: Distinct suppliers issuing invoices to the vendor up to $T_k$.
- `customer_count`: Distinct buyers receiving invoices from the vendor up to $T_k$.
- `relationships`: Top trading ties ordered by financial volume and tax quantum.

### 2. Commercial Concentration
- `largest_supplier_share_pct`: Percentage of inward invoice value from the single largest supplier.
- `largest_customer_share_pct`: Percentage of outward invoice value to the single largest customer.

### 3. Reciprocal Bilateral Trading
Detects instances where vendor $A$ both buys from and sells to counterparty $B$ ($A \to B$ and $B \to A$). In tax auditing, bilateral loops often indicate accommodation billing to artificially inflate commercial turnover.

### 4. Directed Circular Syndicate Loops
Identifies directed simple cycles of length $L \in [3, 5]$ ($A \to B \to C \to A$) characteristic of missing trader intra-community (MTIC) circular fraud schemes.

### 5. Empty-Graph Handling
If a vendor has no recorded commercial ties in the historical snapshot, the engine returns a clean, transparent message:
`"No meaningful graph relationships were available for this vendor-period."`
The engine never fabricates artificial graph metrics or synthetic scores.
