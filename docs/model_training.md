# Machine Learning Model Training & Optimization Protocol

## 1. Experimental Training Framework

### Chronological Train-Validation-Test Splitting
To replicate real-world operational deployment, the benchmark strictly enforces non-overlapping temporal partitioning:

```
Full Benchmark Horizon (24 Months: 2024-05 to 2026-03)
┌──────────────────────────────────────┬─────────────────┬─────────────────┐
│              TRAINING                │   VALIDATION    │      TEST       │
│        2024-05 → 2025-07             │2025-08 → 2025-11│2025-12 → 2026-03│
│        (30,225 samples)              │ (8,060 samples) │ (8,060 samples) │
└──────────────────────────────────────┴─────────────────┴─────────────────┘
```

1. **Training Set ($N = 30,225$)**: Used exclusively for feature imputation parameter fitting, scaling parameter fitting, and model parameter optimization.
2. **Validation Set ($N = 8,060$)**: Used exclusively for model selection, hyperparameter tuning, probability threshold calibration, and early stopping.
3. **Test Set ($N = 8,060$)**: Held out completely untouched until final evaluation. Test distributions and metrics are never exposed to any tuning loop.

---

## 2. Model Candidates & Architectures

### 1. Baselines
- **Majority Class Baseline**: Always predicts the majority class (`LOW`). Serves as the trivial lower bound for accuracy ($72.95\%$) and balanced accuracy ($33.33\%$).
- **Rule-Based Baseline**: Implements statutory penalty logic from Phase 1.5:
  $$\text{Score} = 0.35 \cdot \text{mismatch\_rate} + 0.30 \cdot \min(1.0, \text{delay}/15) + 0.20 \cdot \text{unfiled\_ratio} + 0.15 \cdot \min(1.0, \text{itc\_ratio})$$
  Evaluated with thresholds $< 0.20 \implies \text{LOW}$, $0.20 \le s < 0.50 \implies \text{MEDIUM}$, $\ge 0.50 \implies \text{HIGH}$.

### 2. Model A: Tabular Machine Learning
- **Multinomial Logistic Regression**: $L_2$-regularized multinomial linear model.
- **Random Forest Classifier**: Ensemble of 100 balanced decision trees with max depth 12 and class weight balancing.
- **Tabular XGBoost Classifier**: Gradient boosted trees operating across the 19 tabular features.

### 3. Model B: Graph-Enhanced Machine Learning
- **Graph-Enhanced XGBoost Classifier**: Gradient boosted trees operating across the complete 29-feature representation (19 tabular + 10 temporal graph features).

---

## 3. Hyperparameter Tuning & Selection
Hyperparameters were evaluated on the Training split and ranked strictly by Validation Macro F1 score:

| Hyperparameter Space | Search Values | Selected Value |
|:---|:---|:---:|
| `learning_rate` | $[0.03, 0.05, 0.10]$ | **`0.05`** |
| `max_depth` | $[4, 6, 8]$ | **`6`** |
| `n_estimators` | $[150, 200, 300]$ | **`200`** |
| `subsample` | $[0.8, 1.0]$ | **`0.8`** |
| `colsample_bytree` | $[0.8, 1.0]$ | **`0.8`** |
| `objective` | `multi:softprob` | `multi:softprob` |
| `eval_metric` | `mlogloss` | `mlogloss` |

---

## 4. Multi-Seed Stability & Robustness Protocol
To ensure findings reflect systemic model capabilities rather than stochastic sampling artifacts, evaluations were conducted across 5 random seeds:
$$\mathcal{S} = \{42, 123, 2024, 999, 7\}$$

Each model undergoes the full pipeline:
$$\text{Fit on Train}(\text{seed}) \to \text{Evaluate on Validation} \to \text{Final Scoring on Test}(\text{seed})$$

Mean and standard deviation across seeds are recorded in `data/reports/ml/model_comparison.json`.
