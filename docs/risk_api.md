# GST ITC Risk Engine API Specification

## 1. Overview
The GST ITC Risk Engine exposes RESTful endpoints for real-time risk assessment, financial exposure evaluation, multi-domain evidence review, and historical trend inspection.

---

## 2. Endpoints

### 1. Vendor Risk Prediction
- **Endpoint**: `POST /risk/predict` (also aliased at `POST /api/risk/predict`)
- **Method**: `POST`
- **Request Body**:
```json
{
  "vendor_id": "V1023",
  "period": "2026-03"
}
```

- **Response Schema (`200 OK`)**:
```json
{
  "vendor_id": "V1023",
  "prediction_period": "2026-03",
  "risk": {
    "model_class": "HIGH",
    "risk_band": "HIGH",
    "score": 82.4,
    "probabilities": {
      "LOW": 0.06,
      "MEDIUM": 0.12,
      "HIGH": 0.82
    }
  },
  "itc": {
    "total_invoice_value": 450000.0,
    "total_tax": 81000.0,
    "exposure": 125000.0,
    "exposure_ratio": 0.31
  },
  "evidence": {
    "reconciliation": [
      {
        "type": "RECONCILIATION",
        "feature": "mismatch_rate",
        "value": 0.28,
        "severity": "HIGH",
        "description": "Mismatch rate of 28.0% exceeds high risk threshold (20.0%)."
      }
    ],
    "compliance": [
      {
        "type": "COMPLIANCE",
        "feature": "average_filing_delay",
        "value": 14.5,
        "severity": "HIGH",
        "description": "Chronic filing delay averaging 14.5 days past the statutory due date."
      }
    ],
    "transaction": [
      {
        "type": "TRANSACTION",
        "feature": "itc_exposure",
        "value": 125000.0,
        "severity": "HIGH",
        "description": "Substantial ITC exposure of ₹125,000.00 at risk of tax authority clawback."
      }
    ],
    "model": [
      {
        "type": "MODEL",
        "feature": "average_filing_delay",
        "value": 14.5,
        "severity": "HIGH",
        "description": "Model Tree SHAP attribution: 'average_filing_delay' (val=14.5) increases_risk with impact +0.4520."
      }
    ],
    "graph": [
      {
        "type": "GRAPH",
        "feature": "network_connectivity",
        "value": {"suppliers": 4, "customers": 2},
        "severity": "INFORMATIONAL",
        "description": "Trading network: 4 upstream suppliers, 2 downstream buyers identified."
      }
    ]
  },
  "graph_context": {
    "supplier_count": 4,
    "customer_count": 2,
    "relationships": [
      {
        "counterparty_id": "V0045",
        "direction": "INWARD (Supplier)",
        "invoice_count": 12,
        "total_value": 250000.0,
        "total_tax": 45000.0
      }
    ],
    "largest_supplier_share_pct": 55.6,
    "largest_customer_share_pct": 72.3,
    "reciprocal_count": 0,
    "network_flags": [],
    "temporal_cutoff": "2026-03"
  },
  "recommendations": {
    "review_priority": "CRITICAL",
    "action": "Priority audit and Rule 36(4) ITC blockage review",
    "details": "Vendor exhibits severe non-compliance risk coupled with major financial exposure (₹125,000.00). Initiate statutory inspection."
  },
  "model": {
    "name": "Tabular XGBoost (Frozen)",
    "version": "3.0.0"
  },
  "explanation_text": "Vendor V1023 is classified as HIGH risk..."
}
```

---

### 2. Latest Vendor Assessment
- **Endpoint**: `GET /risk/vendor/{vendor_id}`
- **Query Parameter**: `period` (optional, default `"2026-03"`)
- **Response**: Full production risk assessment for specified vendor and period.

---

### 3. Chronological Vendor Risk History
- **Endpoint**: `GET /risk/vendor/{vendor_id}/history`
- **Method**: `GET`
- **Response Schema (`200 OK`)**:
```json
{
  "vendor_id": "V0001",
  "trend": "stable",
  "transitions": [
    {
      "period_transition": "2024-04 -> 2024-05",
      "class_transition": "LOW -> LOW",
      "score_delta": 1.78
    }
  ],
  "history": [
    {
      "period": "2024-04",
      "risk_class": "LOW",
      "risk_band": "LOW",
      "risk_score": 1.2,
      "itc_exposure": 0.0,
      "mismatch_rate": 0.0
    }
  ]
}
```
