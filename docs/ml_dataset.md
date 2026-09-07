# ML Dataset Specification & Phase 2 Architecture Roadmap

> [!NOTE]
> **Data Provenance Notice**  
> The system uses a hybrid dataset consisting of publicly available transaction data and controlled synthetic GST-specific records. Public data provides realistic transaction distributions, while synthetic data introduces GST-specific filing, reconciliation, ITC, and compliance scenarios that are not available in most public datasets.

---

## 1. Feature Glossary (`vendor_period_features.parquet`)

The tabular feature matrix generated at `data/processed/vendor_period_features.parquet` contains the following attributes per vendor per tax period:

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `vendor_id` | `str` | Vendor identifier |
| `tax_period` | `str` | Observation tax period $T_k$ |
| `invoice_count` | `int` | Total invoices issued in observation period |
| `total_invoice_value` | `float` | Cumulative gross transaction volume (₹) |
| `average_invoice_value` | `float` | Mean invoice ticket size (₹) |
| `total_tax` | `float` | Total tax declared across invoices |
| `mismatch_count` | `int` | Number of invoices with reconciliation discrepancies |
| `mismatch_rate` | `float` | Proportion of invoices with discrepancies ($0.0 \dots 1.0$) |
| `missing_gstr1_count` | `int` | Count of unfiled sales returns in observation period |
| `missing_gstr3b_count` | `int` | Count of unfiled tax payment returns (unpaid tax risk) |
| `late_filing_count` | `int` | Number of returns filed past statutory deadlines |
| `average_filing_delay` | `float` | Mean filing delay in days |
| `duplicate_invoice_count`| `int` | Count of duplicate/near-duplicate submissions |
| `missing_einvoice_count`| `int` | Count of B2B invoices lacking electronic IRN |
| `missing_eway_bill_count`| `int` | Count of consignments > ₹50,000 lacking e-Way Bill |
| `itc_exposure` | `float` | Total input tax credit at financial risk (₹) |
| `supplier_relationship_count`| `int` | Number of distinct active trading counterparties |
| `graph_degree` | `int` | Network node degree in supply graph |
| `graph_centrality` | `float` | Graph connectivity / PageRank centrality |
| `previous_period_risk` | `float` | Prior historical risk score ($T_{k-1}$) |
| **`target_period`** | `str` | Future evaluation period $T_{k+1}$ (Label metadata) |
| **`target_compliance_score`**| `float` | Ground-truth compliance score in $T_{k+1}$ ($0.0 \dots 1.0$) |
| **`target_risk_score`** | `float` | Ground-truth non-compliance risk ($1.0 - \text{Score}$) |
| **`target_risk_label`** | `str` | Supervised classification target: `Low`, `Medium`, `High` |
| **`target_explanation`**| `str` | Human-readable rationale of future statutory infractions |

---

## 2. Recommended Time-Based Data Splitting Strategy

To mirror production deployment where models must predict upcoming periods on unseen future dates:

```text
Full 12-Month Simulated Dataset (2024-04 to 2025-03)
├── Training Set:       Months 1 to 8   (2024-04 to 2024-11)
├── Validation Set:     Months 9 to 10  (2024-12 to 2025-01)
└── Out-of-Time Test:   Months 11 to 12 (2025-02 to 2025-03)
```

Never use random train-test splitting across time periods, as this leaks future macro patterns into past training rows.

---

## 3. Recommended Phase 2 ML Architecture

When proceeding to Phase 2 model training, the following dual-stream architecture is recommended:

```text
               Tabular Features (16+ features)
                     │
                     ▼
          Gradient Boosted Decision Trees
           (XGBoost / LightGBM / CatBoost)
                     │
                     ├──► Multi-Task Probability Outputs:
                     │    1. Risk Classification (Low / Med / High)
                     │    2. Probability of GSTR-3B Tax Default
                     │    3. Expected Discrepancy Amount
                     │
          Relational Knowledge Graph (Neo4j)
                     │
                     ▼
         Graph Neural Network (GNN / GraphSAGE)
           - Node embeddings from trading topology
           - Circular transaction cycle detection
```
