# Phase 2.1: Five-Seed Statistical Validation Report

## 1. Controlled Experiment Overview
- **Model A**: Tabular XGBoost (19 features)
- **Model B**: Graph-Enhanced XGBoost (19 tabular + 10 graph = 29 features)
- **Seeds Evaluated**: `[42, 123, 2024, 999, 7]`
- **Protocol**: Strictly Train (2024-05 → 2025-07) → Validation selection (2025-08 → 2025-11) → Test evaluation (2025-12 → 2026-03).

## 2. Statistical Comparison (Mean ± SD, Min, Max, Delta)

| Metric | Tabular XGB (Mean ± SD) | Graph XGB (Mean ± SD) | Absolute Δ | Relative Improvement (%) | Tabular [Min, Max] | Graph [Min, Max] |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Macro F1** | 0.7404 ± 0.0013 | 0.7400 ± 0.0026 | **-0.0004** | -0.05% | [0.7381, 0.742] | [0.736, 0.7437] |
| **Macro Precision** | 0.7272 ± 0.0011 | 0.7271 ± 0.0026 | **-0.0001** | -0.01% | [0.7252, 0.7282] | [0.7233, 0.7307] |
| **Macro Recall** | 0.7616 ± 0.0021 | 0.7603 ± 0.0025 | **-0.0013** | -0.17% | [0.7595, 0.7646] | [0.7575, 0.7638] |
| **Balanced Accuracy** | 0.7616 ± 0.0021 | 0.7603 ± 0.0025 | **-0.0013** | -0.17% | [0.7595, 0.7646] | [0.7575, 0.7638] |
| **Accuracy** | 0.8712 ± 0.0010 | 0.8712 ± 0.0014 | **+0.0000** | +0.00% | [0.8699, 0.8725] | [0.8694, 0.8733] |
| **Weighted F1** | 0.8758 ± 0.0007 | 0.8756 ± 0.0011 | **-0.0002** | -0.02% | [0.8747, 0.8766] | [0.8741, 0.8772] |
| **High Risk Precision** | 0.4917 ± 0.0047 | 0.4929 ± 0.0100 | **+0.0012** | +0.24% | [0.483, 0.496] | [0.4823, 0.5093] |
| **High Risk Recall** | 0.6519 ± 0.0117 | 0.6473 ± 0.0132 | **-0.0046** | -0.71% | [0.6362, 0.6623] | [0.6319, 0.6638] |
| **High Risk F1** | 0.5605 ± 0.0033 | 0.5594 ± 0.0038 | **-0.0011** | -0.20% | [0.5575, 0.5652] | [0.554, 0.564] |
| **Log Loss** | 0.4113 ± 0.0028 | 0.4104 ± 0.0026 | **-0.0009** | -0.22% | [0.4078, 0.4142] | [0.4081, 0.4136] |
| **Brier Score** | 0.2072 ± 0.0016 | 0.2070 ± 0.0015 | **-0.0002** | -0.10% | [0.2052, 0.2089] | [0.2051, 0.2084] |

## 3. Paired-Seed Comparison

| Seed | Tabular Macro F1 | Graph Macro F1 | Δ Macro F1 | Tabular High-Risk Recall | Graph High-Risk Recall | Δ High-Risk Recall |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 42 | 0.7381 | 0.7393 | **+0.0012** | 0.6594 | 0.6319 | -0.0275 |
| 123 | 0.7408 | 0.7437 | **+0.0029** | 0.6391 | 0.6319 | -0.0072 |
| 2024 | 0.7406 | 0.7360 | **-0.0046** | 0.6623 | 0.6507 | -0.0116 |
| 999 | 0.7406 | 0.7419 | **+0.0013** | 0.6362 | 0.6638 | +0.0276 |
| 7 | 0.7420 | 0.7389 | **-0.0031** | 0.6623 | 0.6580 | -0.0043 |

- **Mean Δ Macro F1**: `-0.0005`
- **Std Δ Macro F1**: `0.0029`
- **Paired t-test p-value**: `0.7648`
- **Wilcoxon signed-rank p-value**: `0.8125`
- **Note**: Five random seeds provide limited statistical sample size (N=5). While paired differences quantify reproducibility across splits, p-values should be interpreted with caution.
