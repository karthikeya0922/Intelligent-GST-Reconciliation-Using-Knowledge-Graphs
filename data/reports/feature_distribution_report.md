# Feature Distribution & Statistical Validation Report

## 1. Numerical Feature Statistics

| Feature | Count | Mean | Median | Std | Min | Max | P25 | P75 | Missing |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `invoice_count` | 46345 | 3.4779 | 3.0 | 1.2431 | 0.0 | 10.0 | 2.0 | 4.0 | 0 |
| `total_invoice_value` | 46345 | 464,976.5625 | 380,504.26 | 415,541.821 | 0.0 | 12,432,127.74 | 239,820.29 | 568,530.33 | 0 |
| `average_invoice_value` | 46345 | 144,571.9119 | 107,349.43 | 210,931.9798 | 0.0 | 8,633,225.41 | 77,141.87 | 151,141.75 | 0 |
| `total_tax` | 46345 | 66,945.3098 | 53,669.81 | 62,492.4424 | 0.0 | 1,577,931.34 | 32,977.07 | 82,018.05 | 0 |
| `mismatch_count` | 46345 | 1.2416 | 1.0 | 1.6188 | 0.0 | 10.0 | 0.0 | 2.0 | 0 |
| `mismatch_rate` | 46345 | 0.3467 | 0.2 | 0.4158 | 0.0 | 1.0 | 0.0 | 1.0 | 0 |
| `missing_gstr1_count` | 46345 | 0.0745 | 0.0 | 0.2626 | 0.0 | 1.0 | 0.0 | 0.0 | 0 |
| `missing_gstr3b_count` | 46345 | 0.0795 | 0.0 | 0.2706 | 0.0 | 1.0 | 0.0 | 0.0 | 0 |
| `late_filing_count` | 46345 | 0.5471 | 1.0 | 0.4978 | 0.0 | 1.0 | 0.0 | 1.0 | 0 |
| `average_filing_delay` | 46345 | 6.92 | 1.0 | 10.6281 | 0.0 | 55.0 | 0.0 | 9.0 | 0 |
| `duplicate_invoice_count` | 46345 | 0.0448 | 0.0 | 0.3656 | 0.0 | 5.0 | 0.0 | 0.0 | 0 |
| `missing_einvoice_count` | 46345 | 0.3154 | 0.0 | 0.7026 | 0.0 | 5.0 | 0.0 | 0.0 | 0 |
| `missing_eway_bill_count` | 46345 | 0.2354 | 0.0 | 0.575 | 0.0 | 5.0 | 0.0 | 0.0 | 0 |
| `itc_exposure` | 46345 | 13,788.5963 | 0.0 | 39,810.397 | 0.0 | 1,316,932.69 | 0.0 | 6,500.0 | 0 |
| `supplier_relationship_count` | 46345 | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0 |
| `graph_degree` | 46345 | 1.0546 | 1.0 | 0.3274 | 1.0 | 4.0 | 1.0 | 1.0 | 0 |
| `previous_period_risk` | 46345 | 0.1333 | 0.035 | 0.211 | 0.0 | 0.9 | 0.0 | 0.1983 | 0 |

## 2. Statistical Distribution Health Checks

- **[WARNING]** supplier_relationship_count: Feature 'supplier_relationship_count' has near-zero variance (std=0.000000).
- **[WARNING]** graph_degree <-> graph_centrality: Features 'graph_degree' and 'graph_centrality' have suspiciously high correlation (r=1.0000).
- **[WARNING]** target_compliance_score <-> target_risk_score: Features 'target_compliance_score' and 'target_risk_score' have suspiciously high correlation (r=1.0000).

## 3. Public vs Synthetic Distribution Compatibility

- **Public Transactions Analyzed**: 50 (Mean: ₹1,763.15, Median: ₹1,160.5)
- **Synthetic Transactions Analyzed**: 168,163 (Mean: ₹114,347.97, Median: ₹76,257.48)
- **Compatibility Status**: `WARNING`
> **Warning**: Significant scale difference: mean transaction values differ by 64.9x.