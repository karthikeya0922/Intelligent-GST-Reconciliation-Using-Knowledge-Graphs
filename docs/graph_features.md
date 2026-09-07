# Knowledge Graph Feature Engineering & Network Topology Specification

## 1. Graph Construction Principles
The GST Knowledge Graph represents B2B commercial relationships as a directed multigraph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$. 
- **Nodes ($\mathcal{V}$)**: Taxpayers / Vendors identified by unique GSTINs or Vendor IDs.
- **Edges ($\mathcal{E}$)**: Commercial invoicing relationships $(u, v)$ directed from supplier $u$ to recipient $v$, weighted by invoice count and tax value.

To satisfy strict temporal leakage prevention, graph metrics are never computed on a static, all-time graph. Instead, for each monthly evaluation period $T_k$, a historical graph snapshot is built:

$$\mathcal{G}_{T_k} = (\mathcal{V}_{T_k}, \mathcal{E}_{T_k}), \quad \mathcal{E}_{T_k} = \{e = (u, v, t) \in \mathcal{E} \mid t \le T_k\}$$

Any trade interaction occurring after $T_k$ is strictly omitted from the snapshot.

---

## 2. Graph Feature Definitions

### 1. In-Degree (`graph_in_degree`)
- **Definition**: Number of distinct suppliers issuing invoices to vendor $v$ in $\mathcal{G}_{T_k}$.
- **Formula**: $k_{\text{in}}(v) = \vert \{u \in \mathcal{V} \mid (u, v) \in \mathcal{E}_{T_k}\} \vert$
- **Tax Intuition**: Measures upstream supply chain diversity. A sudden spike in in-degree from newly formed entities is a hallmark of bogus bill dumping.

### 2. Out-Degree (`graph_out_degree`)
- **Definition**: Number of distinct buyers receiving invoices from vendor $v$ in $\mathcal{G}_{T_k}$.
- **Formula**: $k_{\text{out}}(v) = \vert \{w \in \mathcal{V} \mid (v, w) \in \mathcal{E}_{T_k}\} \vert$
- **Tax Intuition**: High out-degree with minimal input invoices indicates potential invoice mill behavior (generating outward tax liabilities without genuine input tax base).

### 3. Total Degree (`graph_total_degree`)
- **Definition**: Total trading counterparties of vendor $v$.
- **Formula**: $k_{\text{tot}}(v) = k_{\text{in}}(v) + k_{\text{out}}(v)$

### 4. Degree Centrality (`graph_degree_centrality`)
- **Definition**: Normalized connectivity of vendor $v$ relative to the maximum possible connections in snapshot $\mathcal{G}_{T_k}$.
- **Formula**: $C_D(v) = \frac{k_{\text{tot}}(v)}{\vert \mathcal{V}_{T_k} \vert - 1}$
- **Tax Intuition**: Highly central nodes occupy hub positions in the supply network; their default impacts multiple downstream ITC claimants.

### 5. PageRank (`graph_pagerank`)
- **Definition**: Structural authority and prestige score in directed invoice flows with standard damping factor $d = 0.85$.
- **Formula**: $PR(v) = \frac{1-d}{\vert \mathcal{V} \vert} + d \sum_{u \in \mathcal{N}_{\text{in}}(v)} \frac{PR(u)}{k_{\text{out}}(u)}$
- **Tax Intuition**: Quantifies whether a taxpayer receives input supplies from well-established, highly connected entities or from peripheral, fly-by-night operators.

### 6. Local Clustering Coefficient (`graph_clustering_coefficient`)
- **Definition**: Ratio of actual edges between neighbors of $v$ to the maximum possible edges between them (evaluated on the undirected projection).
- **Formula**: $C(v) = \frac{2 e_{\mathcal{N}(v)}}{k_v (k_v - 1)}$
- **Tax Intuition**: High clustering indicates closed, tight trading syndicates. In fraud networks, tight clusters frequently conceal circular accommodation billing.

### 7. Reciprocal Trade Count (`reciprocal_trade_count`)
- **Definition**: Number of counterparties with whom vendor $v$ both buys and sells.
- **Formula**: $R(v) = \vert \{u \in \mathcal{V} \mid (v, u) \in \mathcal{E}_{T_k} \land (u, v) \in \mathcal{E}_{T_k}\} \vert$
- **Tax Intuition**: Mutual buying and selling between the same pair of entities often signals artificial volume generation to inflate turnover for working capital loans or bogus ITC generation.

### 8. Cycle Participation (`cycle_participation`)
- **Definition**: Binary indicator ($1$ or $0$) denoting whether vendor $v$ is a node in a directed simple cycle of length $L \in [3, 5]$.
- **Formula**: $\mathbb{I}\left(v \in \bigcup_{c \in \text{Cycles}(\mathcal{G}_{T_k}, 3 \le \text{len} \le 5)} c\right)$
- **Tax Intuition**: Circular trading is the classic GST fraud schema where invoices circulate through $A \to B \to C \to A$ with no actual underlying goods movement.

### 9. High-Risk Neighbor Count (`high_risk_neighbor_count`)
- **Definition**: Count of adjacent trading partners that were classified as `HIGH` risk in historical periods $\le T_k$.
- **Formula**: $N_{\text{high}}(v) = \vert \{u \in \mathcal{N}(v) \mid \text{HistoricalRisk}(u, \le T_k) = \text{HIGH}\} \vert$
- **Non-Leakage Enforcement**: Evaluated strictly on the latest available risk state prior to or at $T_k$. Never uses $T_{k+1}$ ground-truth risk.

### 10. Neighbor Average Risk (`neighbor_average_risk`)
- **Definition**: Mean historical risk score across all immediate commercial counterparties $\mathcal{N}(v)$.
- **Formula**: $\bar{R}_{\mathcal{N}}(v) = \frac{1}{\vert \mathcal{N}(v) \vert} \sum_{u \in \mathcal{N}(v)} \text{HistoricalRisk}(u, \le T_k)$
- **Default / Neutral**: When a vendor has no prior network neighbors or counterparties with historical ratings, this defaults to neutral $0.0$.
