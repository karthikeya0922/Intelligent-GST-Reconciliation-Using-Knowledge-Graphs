# Phase 2.1: Knowledge Graph Feature Group Ablation Study

> [!NOTE]
> All feature group selections were evaluated on the Validation set without test set feedback.
> Final metrics reflect the locked configurations evaluated once on the held-out Test set.

## 1. Forward Group Addition

| Stage | Active Features | Val Macro F1 | Test Macro F1 | Test Balanced Acc | Test High-Risk Recall | Test High-Risk F1 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Stage 0: Tabular Only (19 features)** | 19 | 0.7254 | 0.7381 | 0.7607 | 0.6594 | 0.5576 |
| **Stage 1: Tabular + Group A [Degree] (22 features)** | 22 | 0.7219 | 0.7412 | 0.7632 | 0.6580 | 0.5619 |
| **Stage 2: Tabular + Group A+B [Centrality] (24 features)** | 24 | 0.7219 | 0.7380 | 0.7606 | 0.6580 | 0.5581 |
| **Stage 3: Tabular + Group A+B+C [Relationship] (25 features)** | 25 | 0.7226 | 0.7407 | 0.7633 | 0.6638 | 0.5630 |
| **Stage 4: Tabular + Group A+B+C+D [Cycles/Clusters] (27 features)** | 27 | 0.7244 | 0.7361 | 0.7581 | 0.6493 | 0.5534 |
| **Stage 5: Tabular + All Graph Groups [A-E] (29 features)** | 29 | 0.7237 | 0.7402 | 0.7621 | 0.6580 | 0.5605 |

## 2. Leave-One-Group-Out Ablation

| Feature Group Removed | Active Features | Val Macro F1 | Test Macro F1 | Test Balanced Acc | Test High-Risk Recall | Test High-Risk F1 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Leave-Out Group A (Degree)** | 26 | 0.7262 | 0.7443 | 0.7666 | 0.6681 | 0.5695 |
| **Leave-Out Group B (Centrality)** | 27 | 0.7246 | 0.7389 | 0.7615 | 0.6580 | 0.5598 |
| **Leave-Out Group C (Relationship Structure)** | 28 | 0.7238 | 0.7415 | 0.7636 | 0.6594 | 0.5642 |
| **Leave-Out Group D (Cycle/Clustering)** | 27 | 0.7244 | 0.7361 | 0.7581 | 0.6493 | 0.5534 |
| **Leave-Out Group E (Historical Neighbor-Risk)** | 27 | 0.7244 | 0.7361 | 0.7581 | 0.6493 | 0.5534 |
