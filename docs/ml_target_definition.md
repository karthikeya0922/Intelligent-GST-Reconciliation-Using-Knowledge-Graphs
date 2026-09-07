# Machine Learning Target Definition: GST Vendor ITC Risk

## 1. Problem Formulation
The GST reconciliation system formulates vendor risk assessment as a multi-period supervised multi-class classification problem. The objective is to forecast a vendor's tax compliance and Input Tax Credit (ITC) default risk for the subsequent statutory filing period ($T_{k+1}$) using transaction, reconciliation, compliance, and network data observed strictly on or before the current period ($T_k$).

$$\hat{y}_{v, T_{k+1}} = f(\mathbf{X}_{v, T_k}, \mathcal{G}_{T_k})$$

Where:
- $v \in \mathcal{V}$ is a registered GST taxpayer / vendor.
- $T_k$ represents the historical observation period (month).
- $\mathbf{X}_{v, T_k} \in \mathbb{R}^D$ is the tabular feature vector at $T_k$.
- $\mathcal{G}_{T_k} = (\mathcal{V}_{T_k}, \mathcal{E}_{T_k})$ is the knowledge graph snapshot containing interactions up to $T_k$.
- $\hat{y}_{v, T_{k+1}} \in \{\text{LOW}, \text{MEDIUM}, \text{HIGH}\}$ is the target risk category for period $T_{k+1}$.

---

## 2. Target Classes & Numerical Encoding
The target variable is `target_risk_next_period`. It is categorized into three mutually exclusive operational risk levels:

| Risk Class | Integer Code | Operational Definition | Enforcement Action |
|:---|:---:|:---|:---|
| **LOW** | `0` | Vendor has regular filings, low discrepancy rate (<5%), full e-Invoice/e-Way Bill adherence, and clean supplier network. | Auto-reconcile invoices, approve ITC claims immediately. |
| **MEDIUM** | `1` | Occasional filing delays, moderate reconciliation discrepancies (5%–25%), or sporadic missing documentation without fraudulent intent. | Manual auditor review, hold ITC provisional credit pending vendor response. |
| **HIGH** | `2` | Severe non-compliance, missing GSTR-1/3B returns, circular trading patterns, shell entity connectivity, or severe invoice mismatches (>25%). | Block ITC credit claim under Rule 36(4), initiate GST audit/inspection notice. |

### Label Encoding Scheme
```python
LABEL_TO_INT = {"Low": 0, "Medium": 1, "High": 2}
INT_TO_LABEL = {0: "Low", 1: "Medium", 2: "High"}
```

---

## 3. Ground-Truth Derivation Methodology
Ground-truth labels are established through the canonical risk labeling engine established in Phase 1.5:
1. **Statutory Non-Filing Defaults**: A supplier failing to furnish GSTR-1 or file summary GSTR-3B tax payment for period $T_{k+1}$.
2. **Reconciliation Discrepancies**: High mismatch frequency ($>20\%$) between outward supplies declared and invoices recorded in the buyer's purchase register.
3. **Injected Audit Anomalies**: Synthetic and hybrid fraud typologies injected into $T_{k+1}$ (e.g., circular invoicing loops, missing e-Way bills on high-value consignments, sudden multi-fold volume spikes).
4. **Composite Risk Index**: In Phase 1.5, normalized penalty scoring maps continuous severity into discrete tiers:
   - Penalty Score $< 0.20 \implies \text{LOW}$
   - $0.20 \le \text{Penalty Score} < 0.50 \implies \text{MEDIUM}$
   - $\text{Penalty Score} \ge 0.50 \implies \text{HIGH}$

---

## 4. Empirical Dataset Distribution
The dataset spans 24 chronological months (May 2024 to March 2026) partitioned into non-overlapping splits:

| Split | Period Range | Total Observations | Low Risk (%) | Medium Risk (%) | High Risk (%) |
|:---|:---|:---:|:---:|:---:|:---:|
| **Train** | `2024-05` to `2025-07` (15 months) | 30,225 | 74.1% | 17.5% | 8.4% |
| **Validation** | `2025-08` to `2025-11` (4 months) | 8,060 | 73.5% | 17.9% | 8.6% |
| **Test** | `2025-12` to `2026-03` (4 months) | 8,060 | 73.0% | 18.5% | 8.5% |
| **Full Benchmark** | `2024-05` to `2026-03` (23 periods) | 46,345 | 73.8% | 17.8% | 8.4% |

---

## 5. Strict Non-Leakage Invariants
1. **Temporal Horizon Guarantee**: The label at row $(v, T_k)$ represents the behavior strictly occurring in $T_{k+1}$. It is stored in the column `target_risk_next_period`.
2. **Feature Isolation**: No feature in row $(v, T_k)$ may query, aggregate, or reference any transaction, filing event, or network connection timestamped $> T_k$.
3. **Neighbor Risk Historical Alignment**: For graph features measuring neighboring entity risk (`high_risk_neighbor_count`, `neighbor_average_risk`), the risk assessment of neighbor $u \in \mathcal{N}(v)$ is derived exclusively from historical periods $\le T_k$, never $T_{k+1}$.
