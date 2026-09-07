# Phase 2.1: Tree SHAP Feature Importance Attribution

## 1. Global Attribution Breakdown
- **Tabular Feature Attribution Share**: `99.98%`
- **Graph Feature Attribution Share**: `0.02%`
- **Graph Features in Top 10**: `0` (None)
- **Graph Features in Top 20**: `1` (graph_out_degree)

## 2. Complete Ranked Feature Table

| Rank | Feature | Type | Feature Group | Mean |SHAP| Value |
|:---:|:---|:---:|:---|:---:|
| 1 | `average_filing_delay` | Tabular | Tabular | 0.880460 |
| 2 | `mismatch_severity_index` | Tabular | Tabular | 0.146650 |
| 3 | `late_filing_count` | Tabular | Tabular | 0.135540 |
| 4 | `previous_period_risk` | Tabular | Tabular | 0.102730 |
| 5 | `unfiled_return_ratio` | Tabular | Tabular | 0.091380 |
| 6 | `missing_einvoice_count` | Tabular | Tabular | 0.090220 |
| 7 | `missing_eway_bill_count` | Tabular | Tabular | 0.079910 |
| 8 | `itc_exposure_ratio` | Tabular | Tabular | 0.051610 |
| 9 | `average_invoice_value` | Tabular | Tabular | 0.046270 |
| 10 | `tax_per_invoice` | Tabular | Tabular | 0.043460 |
| 11 | `itc_exposure` | Tabular | Tabular | 0.042490 |
| 12 | `mismatch_rate` | Tabular | Tabular | 0.042440 |
| 13 | `total_invoice_value` | Tabular | Tabular | 0.037390 |
| 14 | `total_tax` | Tabular | Tabular | 0.033350 |
| 15 | `mismatch_count` | Tabular | Tabular | 0.026040 |
| 16 | `duplicate_invoice_count` | Tabular | Tabular | 0.019900 |
| 17 | `invoice_count` | Tabular | Tabular | 0.012480 |
| 18 | `missing_gstr1_count` | Tabular | Tabular | 0.004160 |
| 19 | `missing_gstr3b_count` | Tabular | Tabular | 0.002980 |
| 20 | `graph_out_degree` | Graph | Group A (Degree/Connectivity) | 0.000250 |
| 21 | `graph_total_degree` | Graph | Group A (Degree/Connectivity) | 0.000060 |
| 22 | `graph_degree_centrality` | Graph | Group B (Centrality) | 0.000020 |
| 23 | `graph_in_degree` | Graph | Group A (Degree/Connectivity) | 0.000000 |
| 24 | `graph_pagerank` | Graph | Group B (Centrality) | 0.000000 |
| 25 | `graph_clustering_coefficient` | Graph | Group D (Cycle/Clustering) | 0.000000 |
| 26 | `reciprocal_trade_count` | Graph | Group C (Relationship Structure) | 0.000000 |
| 27 | `cycle_participation` | Graph | Group D (Cycle/Clustering) | 0.000000 |
| 28 | `high_risk_neighbor_count` | Graph | Group E (Historical Neighbor-Risk) | 0.000000 |
| 29 | `neighbor_average_risk` | Graph | Group E (Historical Neighbor-Risk) | 0.000000 |
