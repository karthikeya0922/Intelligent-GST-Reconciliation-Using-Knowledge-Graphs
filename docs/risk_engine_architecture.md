# Production GST ITC Risk Engine Architecture

## 1. System Architecture Overview

Phase 2.1 demonstrated that Tabular XGBoost captures virtually all predictive signal, while the Knowledge Graph functions as a vital relationship investigation and contextual evidence layer.

```text
                        GST TRANSACTION DATA
                                 │
                                 ▼
                        RECONCILIATION ENGINE
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
       HISTORICAL FEATURES                  KNOWLEDGE GRAPH
      (Cutoff: t <= T_k)                 (Cutoff: t <= T_k)
                │                                 │
                ▼                                 ▼
         TABULAR XGBOOST                 INVESTIGATION LAYER
        (Frozen v3.0.0)                  (Relationship Context)
                │                                 │
                ▼                                 │
         RISK PROBABILITIES                       │
                │                                 │
                ▼                                 │
         ML RISK INDICATOR                        │
           (Score: 0-100)                         │
                │                                 │
                ├────────────────┐                │
                ▼                ▼                ▼
          ITC EXPOSURE      EXPLANATION        NETWORK
         (Discrepancies)    (Tree SHAP)        CONTEXT
                │                │                │
                └────────────────┼────────────────┘
                                 ▼
                         DECISION SUPPORT
                                 │
                                 ▼
                             DASHBOARD
```

---

## 2. Core Functional Subsystems

### 1. Frozen Tabular Predictive Pipeline
- **Model**: `models/production/xgboost_model.pkl` (Frozen 19-feature Tabular XGBoost).
- **Preprocessor**: `models/production/preprocessor.pkl` (Median imputation & feature formatting).
- **Temporal Enforcement**: Mandatory assertion rejecting any feature input timestamped $> T_k$.
- **Inference Latency**: Sub-millisecond CPU scoring ($<15\text{ ms}$ complete request turnaround).

### 2. Evidence Engine (`backend/ml/evidence.py`)
Translates continuous features into multi-domain auditable findings across Reconciliation, Compliance, Transaction Scale, Model SHAP drivers, and Graph topology.

### 3. Knowledge Graph Investigation Layer (`backend/ml/graph_investigation.py`)
Constructs dynamic historical graph snapshots $\mathcal{G}(t \le T_k)$ to explore:
- Upstream suppliers and downstream buyers
- Customer/supplier commercial concentration percentages
- Reciprocal bilateral trade loops ($A \to B$ and $B \to A$)
- Circular trading syndicate loops

### 4. Audit Logging (`data/reports/ml/risk_assessment_audit.log`)
Every prediction generates an immutable audit record logging `timestamp`, `vendor_id`, `prediction_period`, `model_version`, `risk_class`, `risk_score`, and `itc_exposure` for regulatory compliance.
