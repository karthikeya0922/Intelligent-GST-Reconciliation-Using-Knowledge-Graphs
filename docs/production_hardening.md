# Production Hardening, Security & Performance

## 1. Security Architecture & Guardrails

* **CORS Policy:** Restricted CORS middleware configured in FastAPI (`allow_origins`, `allow_credentials`, `allow_methods`, `allow_headers`).
* **Environment Variable Isolation:** Secrets and database endpoints (`MONGODB_URI`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) are loaded strictly from environment variables and `.env`. Zero hardcoded credentials exist in source code or Git.
* **Frontend-Backend Separation:** The React frontend communicates strictly with backend REST endpoints (`/risk/*` and `/api/*`). The frontend never has direct access to MongoDB or Neo4j credentials.
* **Input Validation:** Strict Pydantic models for POST payloads and typed FastAPI query/path parameters with regex validation (`^\d{4}-\d{2}$` for tax periods, range checks for scores and pagination).
* **Sanitized Error Handling:** Server-side exceptions are logged securely without leaking stack traces or internal environment variables to clients. HTTP 400, 404, 422, and 500 status codes provide concise, client-safe error messages.

---

## 2. Performance Engineering & Scalability

* **In-Memory Data Access Layer:** `RiskDataStore` holds parquet observations in memory, avoiding redundant disk reads on repeated queries.
* **Vectorized ML Scoring:** Preprocessed feature transformations and XGBoost `predict_proba` run in batch vectorization, scoring all 2,015 vendors in under 25 milliseconds.
* **Server-Side Pagination:** The vendor risk table enforces bounded page sizes ($1 \le \text{page\_size} \le 100$, default 20) with total count and page metadata to prevent massive DOM overhead.
* **Bounded Graph Traversal:** Knowledge Graph exploration is strictly capped at `depth=1` (direct neighbors) or `depth=2` (two-hop ego network). Subgraph generation is bounded to prevent combinatorial explosion across large connected clusters.
* **Optimized Trend Cache:** Vendor historical trend classifications are computed via vectorized in-memory aggregations across periods in ~13ms for the entire portfolio.
