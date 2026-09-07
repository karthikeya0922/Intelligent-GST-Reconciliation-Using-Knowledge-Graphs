# Dashboard Architecture & Technical Design

## 1. System Architecture Diagram

```mermaid
flowchart TD
    subgraph DataLayer [Data Layer]
        Parquet[vendor_period_features.parquet<br/>46,345 observations]
        SampleData[sample_hybrid_dataset.json<br/>Syndicate network edges & invoices]
        MongoDB[(MongoDB System of Record)]
        Neo4j[(Neo4j Context Layer - Optional)]
    end

    subgraph Backend [FastAPI Backend Service :8000]
        DataStore[RiskDataStore<br/>In-memory Cached Query Engine]
        RiskEngine[ITCRiskEngine<br/>Frozen XGBoost & Tree SHAP]
        GraphInvestigator[GraphInvestigator<br/>Time-Safe Graph Snapshot G t<=Tk]
        APIEndpoints[FastAPI REST Endpoints<br/>/risk/summary, /risk/vendors, /risk/vendor/id/graph]
    end

    subgraph Frontend [React 19 + Vite Frontend :5173]
        RiskAPIClient[riskApi.js<br/>Centralized HTTP Client]
        DashboardPage[Dashboard.jsx<br/>KPIs, Matrix, Longitudinal Charts]
        VendorTable[VendorRiskTable.jsx<br/>Search, Sort, Filter, Pagination]
        VendorDetail[VendorDetail.jsx<br/>SHAP, Multi-Domain Evidence]
        InvestigationWS[InvestigationWorkspace.jsx<br/>8-Step Auditor Dossier & Export]
        GraphExplorer[KnowledgeGraphExplorer.jsx<br/>Interactive Force Graph Canvas]
        ITCAnalytics[ITCExposureAnalytics.jsx<br/>Monetary Exposure & Rankings]
        MethodologyPage[Methodology.jsx<br/>Research & Governance Specs]
    end

    Parquet --> DataStore
    SampleData --> GraphInvestigator
    MongoDB -.-> DataStore
    Neo4j -.-> GraphInvestigator
    RiskEngine --> DataStore
    DataStore --> APIEndpoints
    GraphInvestigator --> APIEndpoints

    APIEndpoints --> RiskAPIClient
    RiskAPIClient --> DashboardPage
    RiskAPIClient --> VendorTable
    RiskAPIClient --> VendorDetail
    RiskAPIClient --> InvestigationWS
    RiskAPIClient --> GraphExplorer
    RiskAPIClient --> ITCAnalytics
    RiskAPIClient --> MethodologyPage
```

---

## 2. In-Memory Cached Data Store (`RiskDataStore`)

To satisfy strict sub-100ms dashboard latency requirements across 46,345 records without repetitive disk operations:
1. **Singleton Pattern:** `get_data_store()` maintains a single in-memory state.
2. **Immutable Precomputation:** `_exposure_trend_cache` precomputes the 24-month longitudinal curve on initialization.
3. **Period Dataframe Caching:** When period $T_k$ (e.g. `2026-02`) is queried, batch XGBoost inference runs once in 24ms across all 2,015 vendors, generating 0–100 scores, presentation bands, and operational priorities.
4. **Fast In-Memory Trend Cache:** `_build_vendor_trends()` computes historical trajectory classifications (`stable`, `improving`, `deteriorating`, `volatile`) in 13ms for the entire portfolio.
5. **Dynamic Aggregations:** Summary statistics, risk distributions, and the Risk × Exposure matrix are calculated directly from active records with zero hard-coded constants.

---

## 3. Frontend Architecture

* **Framework:** React 19 + Vite + React Router v7.
* **Component Modularity:** Strict separation between data access (`src/api/riskApi.js`), reusable UI elements (`src/components/ResearchDisclaimer.jsx`), and dedicated route pages (`src/pages/*`).
* **Visual Standards:** Deep navy dark theme, Inter typography, accessible contrast, curated accent tokens (`#f59e0b`, `#3b82f6`, `#22c55e`, `#ef4444`), compact KPI cards, responsive data tables.
* **State Lifecycle:** Every view strictly implements `Loading`, `Success`, `Empty`, and `Error` states with explicit recovery buttons.
