# Phase 2.1: Knowledge Graph Feature Quality Audit

## 1. Feature Quality Statistics (Training + Validation Sets)

| Feature | Missing % | Zero % | Mean | Std | Min | Max | Unique Values | Skewness | Redundancy Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| `graph_in_degree` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |
| `graph_out_degree` | 0.0% | 99.65% | 0.003526 | 0.059278 | 0.0 | 1.0 | 2 | 16.7517 | NEAR-CONSTANT |
| `graph_total_degree` | 0.0% | 99.65% | 0.003526 | 0.059278 | 0.0 | 1.0 | 2 | 16.7517 | NEAR-CONSTANT |
| `graph_degree_centrality` | 0.0% | 99.65% | 0.000392 | 0.006586 | 0.0 | 0.111111 | 2 | 16.7517 | NEAR-CONSTANT |
| `graph_pagerank` | 0.0% | 99.65% | 0.0002 | 0.003359 | 0.0 | 0.056657 | 2 | 16.7517 | NEAR-CONSTANT |
| `graph_clustering_coefficient` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |
| `reciprocal_trade_count` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |
| `cycle_participation` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |
| `high_risk_neighbor_count` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |
| `neighbor_average_risk` | 0.0% | 100.0% | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.0 | CONSTANT |

## 2. Quality Assessment Summary
- **Total Graph Features**: 10
- **Constant Features**: `['graph_in_degree', 'graph_clustering_coefficient', 'reciprocal_trade_count', 'cycle_participation', 'high_risk_neighbor_count', 'neighbor_average_risk']`
- **Near-Constant Features**: `['graph_in_degree', 'graph_out_degree', 'graph_total_degree', 'graph_degree_centrality', 'graph_pagerank', 'graph_clustering_coefficient', 'reciprocal_trade_count', 'cycle_participation', 'high_risk_neighbor_count', 'neighbor_average_risk']`
- **Highly Redundant Features (|r| > 0.85)**: `['graph_out_degree', 'graph_total_degree', 'graph_degree_centrality', 'graph_pagerank']`
- **Heavily Skewed Features (|skew| > 3)**: `['graph_out_degree', 'graph_total_degree', 'graph_degree_centrality', 'graph_pagerank']`
