# Backend API Specification & Frontend Integration

## 1. Overview

All Phase 4 endpoints provide typed responses, input validation, and standardized error codes. Every endpoint is available under both `/risk/*` and `/api/risk/*` prefixes.

---

## 2. API Endpoints

### 2.1 GET `/risk/summary`
Retrieves dynamically aggregated summary statistics for the portfolio.

* **Query Parameters:**
  * `period` (optional string): Tax period formatted as `YYYY-MM`. Defaults to latest available (`2026-02`).
* **Status Codes:**
  * `200 OK`: Successful summary payload.
  * `400 Bad Request`: Invalid period format.
  * `500 Internal Error`: Backend aggregation failure.
* **Response Payload Schema:**
  ```json
  {
    "period": "2026-02",
    "total_vendors": 2015,
    "risk_distribution": { "LOW": 1420, "MEDIUM": 370, "HIGH": 225 },
    "risk_percentages": { "LOW": 70.47, "MEDIUM": 18.36, "HIGH": 11.17 },
    "band_distribution": { "LOW": 1383, "MEDIUM": 348, "HIGH": 284 },
    "total_itc_exposure": 26871137.88,
    "average_itc_exposure": 13335.55,
    "high_risk_itc_exposure": 9412350.12,
    "exposure_by_risk_class": { "LOW": 5120400.20, "MEDIUM": 12338387.56, "HIGH": 9412350.12 },
    "operational_priority_distribution": { "LOW": 1382, "MEDIUM": 337, "HIGH": 254, "CRITICAL": 42 },
    "risk_exposure_matrix": [
      {
        "risk_band": "HIGH",
        "exposure_tier": "High Exposure",
        "is_high_exposure": true,
        "priority": "CRITICAL",
        "action": "Full investigation and pre-claim audit block",
        "vendor_count": 42,
        "total_exposure": 5420100.00
      }
    ],
    "exposure_over_time": [
      { "period": "2024-04", "total_exposure": 18450200.0, "high_risk_exposure": 3200100.0, "vendor_count": 2015 }
    ]
  }
  ```

---

### 2.2 GET `/risk/vendors`
Provides paginated, filterable, and sortable vendor risk records.

* **Query Parameters:**
  * `search` (string): Text filter matching vendor ID, name, GSTIN, or state.
  * `risk_class` (string): Filter by `LOW`, `MEDIUM`, or `HIGH`.
  * `priority` (string): Filter by `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
  * `min_score`, `max_score` (float): Range [0.0, 100.0].
  * `min_exposure`, `max_exposure` (float): Monetary range in INR.
  * `sort` (string): Column to sort by (`risk_score`, `itc_exposure`, `vendor_id`, `priority`).
  * `order` (string): `asc` or `desc`.
  * `page` (int): 1-indexed page number ($\ge 1$).
  * `page_size` (int): Records per page ($1 \le \text{page\_size} \le 100$).
* **Status Codes:**
  * `200 OK`: Successful paginated list.
  * `400 Bad Request`: Invalid period format.
  * `422 Unprocessable Entity`: Invalid filter parameters or pagination values.

---

### 2.3 GET `/risk/vendor/{vendor_id}/graph`
Extracts interactive multi-hop commercial graph neighborhood.

* **Path Parameters:**
  * `vendor_id` (string): Vendor identifier (e.g., `V0001`).
* **Query Parameters:**
  * `period` (string, default `2026-02`): Temporal cutoff ($t \le \text{period}$).
  * `depth` (int, default `1`): Maximum hop distance (`1` or `2`).
* **Status Codes:**
  * `200 OK`: Nodes, edges, and metadata.
  * `400 Bad Request`: Invalid period format.
  * `404 Not Found`: Vendor not registered in dataset.
  * `422 Unprocessable Entity`: Depth not in `[1, 2]`.

---

### 2.4 GET `/risk/vendor/{vendor_id}`
Returns complete risk profile, Tree SHAP attributions, and multi-domain evidence.

* **Status Codes:**
  * `200 OK`: Complete risk profile.
  * `400 Bad Request`: Invalid period format.
  * `404 Not Found`: Vendor not found.

---

### 2.5 GET `/risk/vendor/{vendor_id}/history`
Returns chronological risk score trajectory and transition events across all available periods.

* **Status Codes:**
  * `200 OK`: History array and trend label (`stable`, `improving`, `deteriorating`, `volatile`).
  * `404 Not Found`: Vendor not found.
