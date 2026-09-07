# GST Risk Feature Catalog & Engineering Specification

## 1. Feature Architecture Overview
The machine learning feature store comprises 29 structured features categorized into 5 distinct operational groups plus derived composite ratios. All features observe a strict information cutoff at period $T_k$, preventing lookahead bias.

```
Total Feature Space: 29 Features
├── Group 1: Transaction Volume & Financial Scale (4 features)
├── Group 2: Reconciliation Discrepancies (5 features)
├── Group 3: Statutory Filing Compliance (4 features)
├── Group 4: Input Tax Credit & Historical State (2 features)
├── Derived Tabular Interaction Ratios (4 features)
└── Group 5: Knowledge Graph Structural & Neighborhood Metrics (10 features)
```

---

## 2. Tabular Feature Definitions

### Group 1: Transaction Features
Captures financial volume, commercial velocity, and invoice scale for vendor $v$ in period $T_k$.

| Feature Name | Type | Description | Imputation / Default |
|:---|:---:|:---|:---:|
| `invoice_count` | `int` | Total number of B2B invoices generated in period $T_k$. | `0.0` |
| `total_invoice_value` | `float` | Cumulative gross taxable invoice amount (INR) in period $T_k$. | `0.0` |
| `average_invoice_value` | `float` | Mean taxable amount per invoice ($\text{total\_value} / \max(\text{count}, 1)$). | `0.0` |
| `total_tax` | `float` | Cumulative CGST + SGST + IGST liability invoiced in period $T_k$. | `0.0` |

### Group 2: Reconciliation Discrepancy Features
Quantifies inconsistencies identified when matching outward supply data against GSTR-2B purchase registers.

| Feature Name | Type | Description | Imputation / Default |
|:---|:---:|:---|:---:|
| `mismatch_count` | `int` | Count of invoices flagged for value, tax, or HSN mismatches. | `0.0` |
| `mismatch_rate` | `float` | Ratio of mismatched invoices to total invoices in period $T_k$. | `0.0` |
| `duplicate_invoice_count` | `int` | Number of duplicate invoice number attempts detected. | `0.0` |
| `missing_einvoice_count` | `int` | Invoices exceeding turnover threshold without mandatory IRN. | `0.0` |
| `missing_eway_bill_count` | `int` | Consignments $> \text{₹}50,000$ moving without an e-Way Bill. | `0.0` |

### Group 3: Statutory Compliance Features
Tracks timeliness and completeness of mandatory GST returns.

| Feature Name | Type | Description | Imputation / Default |
|:---|:---:|:---|:---:|
| `missing_gstr1_count` | `int` | Count of missed outward supply return filings (0 or 1 per month). | `0.0` |
| `missing_gstr3b_count` | `int` | Count of missed summary tax payment return filings (0 or 1 per month).| `0.0` |
| `late_filing_count` | `int` | Returns submitted past the 11th/20th statutory due date. | `0.0` |
| `average_filing_delay` | `float` | Average delay in days past the due date for returns filed in $T_k$. | `0.0` |

### Group 4: Input Tax Credit (ITC) Features
Measures direct financial exposure at risk of tax clawback.

| Feature Name | Type | Description | Imputation / Default |
|:---|:---:|:---|:---:|
| `itc_exposure` | `float` | Quantum of ITC claimed on invoices currently unmatched or missing. | `0.0` |
| `previous_period_risk` | `int` | Vendor risk class in prior period $T_{k-1}$ (0: Low, 1: Med, 2: High). | `0.0` |

---

## 3. Derived Interaction Features
Engineered to capture non-linear risk interactions without expanding model parameter complexity:

$$\text{itc\_exposure\_ratio} = \min\left(1.0, \frac{\text{itc\_exposure}}{\text{total\_tax} + 1.0}\right)$$

$$\text{tax\_per\_invoice} = \frac{\text{total\_tax}}{\max(1.0, \text{invoice\_count})}$$

$$\text{unfiled\_return\_ratio} = \min\left(1.0, \frac{\text{missing\_gstr1\_count} + \text{missing\_gstr3b\_count}}{2.0}\right)$$

$$\text{mismatch\_severity\_index} = \min\left(1.0, 0.7 \cdot \text{mismatch\_rate} + 0.3 \cdot \min\left(1.0, \frac{\text{duplicate\_invoice\_count}}{5.0}\right)\right)$$

---

## 4. Knowledge Graph Structural & Neighborhood Features
Extracted from temporal snapshot graph $\mathcal{G}_{T_k} = (\mathcal{V}_{T_k}, \mathcal{E}_{T_k})$ constructed using only invoices with $\text{period} \le T_k$:

| Feature Name | Graph Semantic | Mathematical Definition |
|:---|:---|:---|
| `graph_in_degree` | Inward supplier connectivity | $\vert \{u \mid (u, v) \in \mathcal{E}_{T_k}\} \vert$ |
| `graph_out_degree` | Outward customer connectivity | $\vert \{w \mid (v, w) \in \mathcal{E}_{T_k}\} \vert$ |
| `graph_total_degree` | Total trading counterparties | $\text{in\_degree} + \text{out\_degree}$ |
| `graph_degree_centrality` | Normalized connectivity in trade network | $C_D(v) = \frac{\text{total\_degree}(v)}{\vert \mathcal{V}_{T_k} \vert - 1}$ |
| `graph_pagerank` | Structural authority in transaction flow | PageRank with damping factor $d = 0.85$ |
| `graph_clustering_coefficient` | Local triadic closure & trading cluster density | Fraction of edges between neighbors of $v$ |
| `reciprocal_trade_count` | Bilateral trade loops (potential accommodation bills) | $\vert \{u \mid (v,u) \in \mathcal{E}_{T_k} \land (u,v) \in \mathcal{E}_{T_k}\} \vert$ |
| `cycle_participation` | Circular transaction loop membership | 1 if $v$ belongs to directed cycle of length 3–5; 0 otherwise |
| `high_risk_neighbor_count` | Exposure to flagged counterparties | $\vert \{u \in \mathcal{N}(v) \mid \text{historical\_risk}(u) = 2\} \vert$ |
| `neighbor_average_risk` | Contagion risk from adjacent trading network | $\frac{1}{\vert \mathcal{N}(v) \vert} \sum_{u \in \mathcal{N}(v)} \text{historical\_risk}(u)$ |

---

## 5. Preprocessing & Scaling Pipeline
1. **Missing Value Imputation**: Median imputation fitted strictly on the Training set (`ColumnTransformer` via `SimpleImputer(strategy='median')`).
2. **Feature Scaling**: Numerical scale normalization applying `RobustScaler` to heavy-tailed financial values (`total_invoice_value`, `total_tax`, `average_invoice_value`, `itc_exposure`) to mitigate sensitivity to extreme corporate outliers without clipping genuine fraud amounts.
