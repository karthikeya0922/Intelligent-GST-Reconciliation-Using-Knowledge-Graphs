# Intelligent GST Reconciliation Using Knowledge Graphs

> **Research-grade GST reconciliation, ITC risk prediction, explainability, and graph-based investigation platform.**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev/)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-orange)](https://xgboost.readthedocs.io/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Knowledge%20Graph-red)](https://neo4j.com/)
[![Tests](https://img.shields.io/badge/Tests-106%20Passing-success)]()

---

## 📌 Overview

**Intelligent GST Reconciliation Using Knowledge Graphs** is a research-oriented platform designed to assist with GST invoice reconciliation, vendor risk assessment, Input Tax Credit (ITC) exposure analysis, and relationship-based investigation.

The system combines:

* GST reconciliation
* Historical behavioral feature engineering
* Machine learning
* Knowledge Graph investigation
* Explainable AI
* ITC exposure analysis
* Temporal leakage prevention
* Auditor-oriented decision support

The system is designed as a **risk-indicator and decision-support platform**, not as a system that determines fraud, tax liability, or statutory non-compliance.

---

# 🎯 Research Question

The primary research question is:

> **Does incorporating Knowledge Graph-derived information improve GST vendor/ITC risk prediction compared with conventional tabular machine-learning models?**

The experimental results provide a neutral answer on the current benchmark:

> **Knowledge Graph-derived predictive features did not provide statistically significant incremental predictive improvement over the tabular XGBoost baseline.**

Rather than forcing the Knowledge Graph into the predictive model, the architecture therefore uses the Knowledge Graph as an **investigative and relationship-context layer**.

---

# 🏗️ System Architecture

```text
                    GST TRANSACTION DATA
                            │
                            ▼
                  RECONCILIATION ENGINE
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
      HISTORICAL FEATURES          KNOWLEDGE GRAPH
              │                           │
              ▼                           ▼
       TABULAR XGBOOST            INVESTIGATION LAYER
              │                           │
              ▼                           │
       RISK PROBABILITIES                 │
              │                           │
              ▼                           ▼
       ML RISK INDICATOR          NETWORK CONTEXT
              │                           │
              └─────────────┬─────────────┘
                            ▼
                     DECISION SUPPORT
                            │
                            ▼
                        DASHBOARD
```

---

# 🔄 End-to-End Pipeline

```text
GST Data
   ↓
Data Normalization
   ↓
Invoice Reconciliation
   ↓
Anomaly Detection
   ↓
Historical Feature Engineering
   ↓
Temporal Train / Validation / Test Split
   ↓
Tabular XGBoost
   ↓
Risk Probability
   ↓
0–100 ML Risk Indicator
   ↓
ITC Exposure Analysis
   ↓
SHAP Explanation
   ↓
Knowledge Graph Investigation
   ↓
Risk × Exposure Prioritization
   ↓
Auditor Decision Support
```

---

# 📊 Research Dataset

The current benchmark is a controlled **hybrid/synthetic research dataset**.

| Component                  |               Value |
| -------------------------- | ------------------: |
| Vendors                    |               2,015 |
| Invoices                   |             168,213 |
| Simulated Periods          |           24 months |
| Vendor-Period Observations |              46,345 |
| Synthetic Invoices         |             168,163 |
| Public Invoices            |                  50 |
| Logged Anomaly Events      |              57,329 |
| Target Classes             | Low / Medium / High |

### Temporal Coverage

```text
2024-04 → 2026-03
```

The dataset is partitioned chronologically to prevent future information from entering earlier predictions.

---

# 🧠 Machine Learning

## Primary Production Model

The production predictive model is:

> **Tabular XGBoost**

The model uses 19 validated tabular features derived from historical GST behavior.

### Feature Groups

#### Transaction

* Invoice count
* Total invoice value
* Average invoice value
* Total tax

#### Reconciliation

* Mismatch count
* Mismatch rate
* Duplicate invoice count
* Missing e-invoice count
* Missing e-way bill count

#### Compliance

* Missing GSTR-1 count
* Missing GSTR-3B count
* Filing delay
* Late filing count

#### ITC

* ITC exposure
* ITC exposure ratio

Additional historical and interaction features are included where applicable.

---

# 📈 Model Comparison

The system evaluated multiple approaches:

1. Majority-class baseline
2. Rule-based baseline
3. Logistic Regression
4. Random Forest
5. Tabular XGBoost
6. Graph-enhanced XGBoost

The graph-enhanced model was evaluated using the same temporal experimental framework as the tabular model.

---

# 🔬 Phase 2.1 Result

The five-seed experiment found essentially no meaningful improvement from adding graph-derived predictive features.

| Metric            | Tabular XGBoost |   Graph XGBoost |
| ----------------- | --------------: | --------------: |
| Macro F1          | 0.7404 ± 0.0013 | 0.7400 ± 0.0026 |
| Balanced Accuracy | 0.7616 ± 0.0021 | 0.7603 ± 0.0025 |
| Accuracy          | 0.8712 ± 0.0010 | 0.8712 ± 0.0014 |
| High-Risk Recall  | 0.6519 ± 0.0117 | 0.6473 ± 0.0132 |
| Log Loss          | 0.4113 ± 0.0028 | 0.4104 ± 0.0026 |

Paired statistical testing produced:

```text
Paired t-test:      p = 0.7648
Wilcoxon test:      p = 0.8125
```

Therefore:

> **The benchmark does not provide evidence that graph-derived predictive features improve the tabular XGBoost model.**

---

# 🕸️ Knowledge Graph

The Knowledge Graph is intentionally separated from the predictive model.

It provides:

* Supplier relationships
* Customer relationships
* Counterparty counts
* Reciprocal trading relationships
* Transaction concentration
* Cycle signals
* Network structure
* Relationship context

The graph is **not used to generate a fraud score**.

Instead, it helps an investigator understand the relationships surrounding a vendor.

---

# ⚠️ Temporal Leakage Prevention

Temporal integrity is a core design requirement.

For a prediction period `Tk`, only information available at or before `Tk` may be used.

```text
Allowed:

transaction_date <= Tk

filing_date <= Tk

relationship.tax_period <= Tk
```

Future information is explicitly blocked.

Graph snapshots also enforce:

```text
relationship.tax_period <= selected_period
```

This prevents future relationships from appearing in historical investigations.

---

# 🎯 Risk Indicator

The production engine generates a deterministic 0–100 ML Risk Indicator:

```text
Risk Score =
100 × (P(MEDIUM) × 0.5 + P(HIGH) × 1.0)
```

The score is then presented using application bands:

|   Score | Band   |
| ------: | ------ |
|    0–33 | LOW    |
|  >33–66 | MEDIUM |
| >66–100 | HIGH   |

The underlying model class and presentation band are intentionally kept separate.

---

# 💰 ITC Exposure

ITC Exposure represents the financial quantity associated with reconciliation discrepancies.

It is **not equivalent to fraud risk**.

The system therefore keeps these concepts separate:

```text
Financial Quantity
        │
        └── ITC Exposure

Behavioral Risk
        │
        └── ML Risk Indicator

Operational Review
        │
        └── Priority

Investigation Context
        │
        └── Knowledge Graph
```

---

# 🚦 Risk × Exposure Prioritization

The system combines behavioral risk and financial exposure to determine operational review priority.

```text
                 ITC EXPOSURE
              Low     Medium     High
           ┌────────┬──────────┬─────────┐
Low Risk   │  LOW   │   LOW    │ MEDIUM  │
           ├────────┼──────────┼─────────┤
Med Risk   │  LOW   │  MEDIUM  │  HIGH   │
           ├────────┼──────────┼─────────┤
High Risk  │ MEDIUM │   HIGH   │ CRITICAL│
           └────────┴──────────┴─────────┘
```

This allows investigators to prioritize cases based on both behavioral risk and financial materiality.

---

# 🔎 Explainability

The system uses **native XGBoost Tree SHAP** for model explanations.

For each vendor, the system can provide:

* Top risk-increasing factors
* Protective factors
* Model probabilities
* Contributing features
* Historical risk trajectory

Example interpretation:

> Average filing delay contributed positively to the model's predicted risk.

The system does **not** claim that a feature caused non-compliance.

---

# 🖥️ Dashboard

The Phase 4 dashboard provides:

### Dashboard

* Total vendors
* Total ITC exposure
* High/Medium/Low risk distribution
* High/Critical priority vendors
* Exposure trends
* Risk × Exposure matrix

### Vendor Risk

* Vendor search
* Risk filtering
* Priority filtering
* Risk score sorting
* ITC exposure sorting
* Pagination

### Vendor Detail

* Risk score
* Model probabilities
* SHAP factors
* Evidence
* Risk history
* Trend
* ITC exposure

### Investigation Workspace

```text
Vendor
 ↓
Risk
 ↓
ITC Exposure
 ↓
SHAP Factors
 ↓
Reconciliation
 ↓
Compliance
 ↓
Knowledge Graph
 ↓
Operational Priority
```

### Knowledge Graph Explorer

* Interactive graph
* Depth 1 / Depth 2
* Temporal period selection
* Supplier/customer relationships
* Reciprocal relationships
* Network context

### ITC Analytics

* Portfolio exposure
* Average exposure
* Exposure by risk
* Historical exposure
* Top vendors by exposure

### Methodology

Documents:

* Dataset
* ML methodology
* Graph methodology
* Phase 2.1 findings
* Explainability
* Research limitations
* Ethical positioning

---

# 🛠️ Technology Stack

## Backend

* Python 3.11
* FastAPI
* Pydantic
* Pandas
* PyArrow
* Scikit-learn
* XGBoost
* NetworkX
* MongoDB
* Neo4j

## Frontend

* React 19
* Vite
* Chart.js
* react-force-graph-2d
* Lucide Icons

## Data

* Parquet
* JSON
* MongoDB
* Neo4j

---

# 🔌 API

## Risk Prediction

```http
POST /risk/predict
POST /api/risk/predict
```

## Risk Summary

```http
GET /risk/summary
GET /api/risk/summary
```

## Vendor Portfolio

```http
GET /risk/vendors
GET /api/risk/vendors
```

Supports:

```text
search
risk_class
priority
min_score
max_score
min_exposure
max_exposure
sort
page
page_size
```

## Vendor Information

```http
GET /risk/vendor/{vendor_id}
GET /risk/vendor/{vendor_id}/history
```

## Knowledge Graph

```http
GET /risk/vendor/{vendor_id}/graph
GET /api/risk/vendor/{vendor_id}/graph
```

Supports:

```text
period
depth
```

---

# 🧪 Testing

The complete automated test suite currently contains:

```text
106 tests
106 passing
0 failing
```

Run:

```bash
python -m pytest
```

The test coverage includes:

* Data validation
* Dataset scaling
* Temporal splitting
* Leakage detection
* Feature engineering
* Model training
* Graph construction
* Graph temporal leakage
* Model persistence
* Predictions
* Explainability
* Risk scoring
* ITC exposure
* Evidence generation
* Risk history
* API endpoints
* Phase 4 integration

---

# 🏃 Running the Project

## Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn backend.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

## Frontend

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

The frontend communicates with the backend through:

```text
VITE_API_URL
```

---

# 📁 Project Structure

```text
Intelligent-GST-Reconciliation-Using-Knowledge-Graphs/
│
├── backend/
│   ├── main.py
│   └── ml/
│       ├── features.py
│       ├── graph_features.py
│       ├── graph_investigation.py
│       ├── risk_engine.py
│       ├── evidence.py
│       ├── explanation.py
│       ├── data_store.py
│       ├── train.py
│       └── predict.py
│
├── data/
│   ├── processed/
│   └── reports/
│
├── models/
│   └── production/
│
├── src/
│   ├── api/
│   ├── components/
│   └── pages/
│
├── tests/
│   ├── data/
│   ├── ml/
│   └── risk_engine/
│
├── docs/
│
├── requirements.txt
├── package.json
└── README.md
```

---

# 🔐 Security & Production Hardening

The system implements:

* Environment-based configuration
* No hardcoded database credentials
* Backend-only database communication
* Pydantic request validation
* Sanitized API errors
* Bounded pagination
* Limited graph depth
* Temporal validation
* Server-side aggregation

---

# ⚠️ Research Limitations

This project is currently a **research prototype**, not a production statutory tax-compliance system.

### Dataset limitation

The benchmark is controlled and hybrid/synthetic.

External validation with appropriately labelled real-world GST data is required.

### Model limitation

The model predicts behavioral risk indicators rather than confirmed fraud.

### Knowledge Graph limitation

The current benchmark did not demonstrate statistically significant predictive improvement from graph-derived features.

The graph is therefore used for investigation and relationship context.

### Generalization limitation

Performance on this benchmark should not be interpreted as guaranteed performance on real-world GST populations.

---

# ⚖️ Ethical Positioning

This system provides:

> **Experimental ML-based risk indicators and decision-support information.**

It does not provide:

* Fraud determinations
* Tax liability determinations
* Statutory non-compliance determinations
* Legal conclusions

Any real-world deployment would require appropriate:

* Real-world validation
* Domain expert review
* Governance
* Privacy controls
* Regulatory compliance
* Human oversight

---

# 📚 Research Documentation

Detailed methodology is available in:

```text
docs/
├── ml_target_definition.md
├── ml_features.md
├── model_training.md
├── model_evaluation.md
├── graph_features.md
├── graph_temporal_methodology.md
├── explainability.md
├── phase2_ml_report.md
├── risk_scoring_methodology.md
├── itc_prioritization_methodology.md
├── risk_engine_architecture.md
├── risk_explainability.md
├── graph_investigation.md
├── risk_api.md
├── phase4_dashboard.md
├── dashboard_architecture.md
├── api_integration.md
├── investigation_workflow.md
├── production_hardening.md
└── research_limitations.md
```

---

# 🧭 Project Phases

```text
Phase 1
  ↓
GST Data Foundation & Reconciliation
  ↓
Phase 1.5
  ↓
Hybrid Dataset Scaling & Validation
  ↓
Phase 2
  ↓
ML Risk Prediction & Graph-Enhanced ML
  ↓
Phase 2.1
  ↓
Statistical Graph Contribution Analysis
  ↓
Phase 3
  ↓
Production ITC Risk Engine & Explainability
  ↓
Phase 4
  ↓
Risk Intelligence Dashboard & Investigation Platform
```

---

# 📌 Current Status

| Component                   | Status        |
| --------------------------- | ------------- |
| GST Data Pipeline           | ✅ Complete    |
| Reconciliation Engine       | ✅ Complete    |
| Dataset Validation          | ✅ Complete    |
| ML Risk Prediction          | ✅ Complete    |
| Temporal Leakage Protection | ✅ Complete    |
| Graph Investigation         | ✅ Complete    |
| Explainability              | ✅ Complete    |
| ITC Exposure Engine         | ✅ Complete    |
| Risk Prioritization         | ✅ Complete    |
| REST API                    | ✅ Complete    |
| Dashboard                   | ✅ Complete    |
| Investigation Workspace     | ✅ Complete    |
| Knowledge Graph Explorer    | ✅ Complete    |
| Methodology Documentation   | ✅ Complete    |
| Automated Tests             | ✅ 106 Passing |
| Frontend Production Build   | ✅ Passing     |

---

# 🚀 Future Work

Potential future research directions include:

* Validation on appropriately labelled real-world GST datasets
* Larger and more diverse vendor populations
* External temporal validation
* Improved network representations
* Graph representation learning if future datasets demonstrate sufficient topology
* Model monitoring and drift detection
* Human-in-the-loop evaluation
* Fairness and subgroup performance analysis
* Production-scale deployment

These are future research directions and are **not part of the current validated system**.

---

# 👨💻 Research Position

The central contribution of this project is not simply adding a Knowledge Graph to an ML model.

Instead, the project experimentally evaluates whether graph-derived information improves predictive performance and, based on the current benchmark, finds that it does not.

The resulting architecture separates:

```text
Prediction
    ↓
Tabular XGBoost

Investigation
    ↓
Knowledge Graph

Financial Materiality
    ↓
ITC Exposure

Operational Decision Support
    ↓
Risk × Exposure Priority
```

This separation provides a more transparent and scientifically defensible approach to GST risk intelligence.

---

## ⚠️ Disclaimer

This project is an experimental research system.

> **This system provides experimental ML-based risk indicators and decision-support information. It is not a determination of fraud, tax liability, or statutory non-compliance. Results are demonstrated on a controlled hybrid research benchmark. External validation using appropriately labelled real-world data is required before operational deployment.**
