# GST ReconcileAI — Complete Project Documentation

> **Project Name:** GST ReconcileAI — Intelligent GST Reconciliation Using Knowledge Graphs  
> **Tech Stack:** React 19 + Vite (Frontend) | FastAPI + Python (Backend) | Neo4j Knowledge Graph (Database)  
> **Date:** February 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [Project Structure](#3-project-structure)
4. [Frontend — React + Vite](#4-frontend--react--vite)
   - 4.1 [App Entry & Routing](#41-app-entry--routing)
   - 4.2 [Login & Authentication](#42-login--authentication)
   - 4.3 [Dashboard Page](#43-dashboard-page)
   - 4.4 [Knowledge Graph Page](#44-knowledge-graph-page)
   - 4.5 [Reconciliation Page](#45-reconciliation-page)
   - 4.6 [ITC Risk Dashboard](#46-itc-risk-dashboard)
   - 4.7 [Audit Trails Page](#47-audit-trails-page)
   - 4.8 [Vendor Compliance Page](#48-vendor-compliance-page)
   - 4.9 [Settings Page](#49-settings-page)
   - 4.10 [Theme System (Dark/Light)](#410-theme-system-darklight)
   - 4.11 [Mock Data](#411-mock-data)
   - 4.12 [CSS & Styling](#412-css--styling)
5. [Backend — FastAPI + Python](#5-backend--fastapi--python)
   - 5.1 [main.py — API Server](#51-mainpy--api-server)
   - 5.2 [reconcile.py — Reconciliation Engine](#52-reconcilepy--reconciliation-engine)
   - 5.3 [risk_model.py — Vendor Risk ML Model](#53-risk_modelpy--vendor-risk-ml-model)
   - 5.4 [explain.py — Audit Trail Generator](#54-explainpy--audit-trail-generator)
   - 5.5 [ingestion.py — Data Ingestion Pipeline](#55-ingestionpy--data-ingestion-pipeline)
6. [API Endpoints](#6-api-endpoints)
7. [How to Run](#7-how-to-run)
8. [Key Features Summary](#8-key-features-summary)

---

## 1. Project Overview

**GST ReconcileAI** is a full-stack web application that uses **Knowledge Graphs** and **Machine Learning** to intelligently reconcile GST (Goods and Services Tax) filings in India. It automatically detects mismatches between GSTR-1 (Sales Return) and GSTR-2B (Purchase Return), predicts vendor compliance risk, and generates explainable audit trails using LLM-powered GraphRAG.

### Core Problem Solved
- Manual GST reconciliation is error-prone and time-consuming
- Businesses lose ITC (Input Tax Credit) worth lakhs due to undetected mismatches
- No automated way to trace WHY an invoice is flagged across the compliance chain

### Solution
- **Knowledge Graph** (Neo4j) links Vendors → Invoices → GSTR Returns → e-Invoices → e-Way Bills
- **Graph traversal** detects mismatches that table-based systems miss
- **RandomForest ML model** predicts vendor risk using graph-derived features
- **LangChain + Neo4j GraphRAG** generates human-readable audit explanations grounded in graph facts

---

## 2. Tech Stack & Dependencies

### Frontend
| Dependency | Version | Purpose |
|---|---|---|
| React | 19.2.0 | UI framework |
| Vite | 7.3.1 | Build tool & dev server |
| react-router-dom | 7.13.1 | Client-side routing |
| framer-motion | 12.34.3 | Animations & transitions |
| chart.js + react-chartjs-2 | 4.5.1 / 5.3.1 | Charts (Line, Bar, Doughnut, Pie, Radar) |
| lucide-react | 0.575.0 | Icons |
| react-force-graph-2d | 1.29.1 | Knowledge graph visualization |

### Backend
| Dependency | Version | Purpose |
|---|---|---|
| FastAPI | 0.104.1 | Python API framework |
| Uvicorn | 0.24.0 | ASGI server |
| neo4j | 5.14.0 | Neo4j database driver |
| pandas | 2.1.4 | Data manipulation |
| scikit-learn | 1.3.2 | ML model (RandomForest) |
| joblib | 1.3.2 | Model persistence |
| langchain | 0.1.0 | LLM orchestration |
| langchain-neo4j | 0.1.0 | Neo4j + LangChain integration |
| langchain-openai | 0.0.2 | OpenAI LLM provider |
| openai | 1.6.0 | GPT API client |
| python-dotenv | 1.0.0 | Environment variable management |

---

## 3. Project Structure

```
klh hackathon/
├── index.html                   # HTML entry point
├── package.json                 # Node.js dependencies
├── vite.config.js               # Vite configuration
├── eslint.config.js             # ESLint configuration
├── public/
│   └── vite.svg                 # Favicon
├── src/
│   ├── main.jsx                 # React DOM entry point
│   ├── App.jsx                  # Root component (routing, layout, sidebar)
│   ├── App.css                  # Minimal app-level styles
│   ├── index.css                # Full design system (30KB, dark/light themes)
│   ├── assets/
│   │   └── react.svg
│   ├── context/
│   │   ├── AuthContext.jsx      # Authentication provider (login/signup/logout)
│   │   └── ThemeContext.jsx     # Dark/Light theme provider
│   ├── data/
│   │   └── mockData.js          # Comprehensive mock data (24KB)
│   └── pages/
│       ├── Dashboard.jsx        # Main dashboard with KPI cards & charts
│       ├── KnowledgeGraph.jsx   # Interactive force-directed graph
│       ├── Reconciliation.jsx   # Invoice mismatch table with filters
│       ├── ITCRisk.jsx          # ITC risk analytics & charts
│       ├── AuditTrails.jsx      # LLM-generated audit explanations
│       ├── VendorCompliance.jsx # Vendor scoring & compliance analysis
│       ├── Settings.jsx         # User profile, theme, notifications, etc.
│       └── LoginPage.jsx        # Auth page (login + signup)
└── backend/
    ├── main.py                  # FastAPI server + API endpoints
    ├── reconcile.py             # Neo4j graph-based reconciliation engine
    ├── risk_model.py            # RandomForest vendor risk model
    ├── explain.py               # LangChain + GraphRAG audit explanations
    ├── ingestion.py             # GSTR-1/2B/e-Invoice data ETL pipeline
    └── requirements.txt         # Python dependencies
```

---

## 4. Frontend — React + Vite

### 4.1 App Entry & Routing

**File:** `src/App.jsx` (151 lines)

The root component wraps the entire app in three providers:
- `BrowserRouter` — client-side routing
- `ThemeProvider` — dark/light theme context
- `AuthProvider` — authentication context

**Routing Table:**

| Route | Component | Description |
|---|---|---|
| `/login` | `LoginPage` | Login / Signup page |
| `/` | `Dashboard` | Main dashboard |
| `/knowledge-graph` | `KnowledgeGraph` | Interactive graph |
| `/reconciliation` | `Reconciliation` | Mismatch table |
| `/itc-risk` | `ITCRisk` | ITC risk analytics |
| `/audit-trails` | `AuditTrails` | AI audit explanations |
| `/vendor-compliance` | `VendorCompliance` | Vendor scoring |
| `/settings` | `Settings` | User settings |

**Sidebar** includes:
- App logo "⚡ GST ReconcileAI" with subtitle "Knowledge Graph Engine"
- User avatar (first letter of name) + user name + role
- Theme toggle button (Sun/Moon icon)
- Navigation links grouped into: **Overview**, **Deliverables**, **System**
- Footer showing "Neo4j Connected" and "LLM Engine Active" status indicators with green dots

**Protected Routes:** All routes except `/login` require authentication. If not logged in, user is redirected to `/login`.

---

### 4.2 Login & Authentication

**File:** `src/pages/LoginPage.jsx` (227 lines)  
**File:** `src/context/AuthContext.jsx` (105 lines)

#### Login Page Features:
- Toggle between **Login** and **Sign Up** forms with animated transitions (framer-motion)
- Input fields: Email, Password (login) + Name (signup) with show/hide password toggle
- **Demo Account Quick-Fill** buttons for Admin and Auditor accounts
- Error message display for invalid credentials
- Left panel with feature highlights: Knowledge Graph, Auto-Reconciliation, Compliance Shield, Predictive AI
- Animated background with floating gradient orbs

#### Auth System (AuthContext):
- Uses **localStorage** as a static database (`gst-users-db`)
- Default accounts pre-seeded:
  - `admin@gstreconcile.ai` / `admin123` (Admin)
  - `auditor@gstreconcile.ai` / `auditor123` (Auditor)
- Functions: `login()`, `signup()`, `logout()`, `updateProfile()`
- Session persistence via `gst-current-user` localStorage key
- Sessions survive page refreshes

---

### 4.3 Dashboard Page

**File:** `src/pages/Dashboard.jsx` (175 lines)

The main overview page with animated KPI cards and charts.

**KPI Cards (4 cards with stagger animation):**
1. **Total Mismatches** — Count of unmatched invoices with red indicator
2. **Tax at Risk (₹)** — Total INR amount at risk, formatted in Indian numbering
3. **Vendors Flagged** — High-risk vendor count with orange indicator
4. **Reconciliation Score** — Percentage of matched invoices with green indicator

**Charts:**
- **Line Chart** — "ITC at Risk vs Total ITC" trend over 6 months (Jan–Sep 2025)
- **Doughnut Chart** — "Mismatches by Type" (Missing in GSTR-1, Tax Amount Mismatch, HSN Mismatch, Late Filing, E-Way Bill Missing)
- **Bar Chart** — "Top Vendors by Risk Score" showing risk scores of flagged vendors

All charts use Chart.js with dark-themed styling (transparent grid lines, Inter font).

---

### 4.4 Knowledge Graph Page

**File:** `src/pages/KnowledgeGraph.jsx` (268 lines)

An **interactive force-directed graph** visualization using `react-force-graph-2d`.

**Node Types (color-coded):**
| Group | Color | Description |
|---|---|---|
| Vendor | `#f59e0b` (Amber) | GST-registered vendor |
| Invoice | `#ef4444` (Red) / `#22c55e` (Green) | Flagged or matched invoice |
| GSTR | `#3b82f6` (Blue) | GSTR return filing |
| e-Invoice | `#8b5cf6` (Purple) | e-Invoice record |
| e-Way Bill | `#06b6d4` (Cyan) | e-Way Bill |

**Edge Types:**
- ISSUED_INVOICE, REPORTED_IN, SUMMARIZED_IN, ELECTRONIC_VERSION, COVERS_SHIPMENT

**Interactive Features:**
- Click a node to select it and see its details in a side panel
- Node details show: ID, label, group, and any extra properties (GSTIN, amount, status)
- Color-coded legend explaining node and edge meanings
- Hover effects on nodes
- Responsive sizing (fills container)
- Stats bar showing total nodes, edges, and node type breakdown

---

### 4.5 Reconciliation Page

**File:** `src/pages/Reconciliation.jsx` (213 lines)

A full-featured **invoice mismatch table** with filtering and search.

**Features:**
- **Summary Cards** at top:
  - Total Mismatches (count)
  - Tax at Risk (₹ formatted)
  - High Risk count
  - Matched count
- **Search Bar** — real-time search by invoice ID, vendor name, GSTIN
- **Filter Dropdown** — filter by mismatch type (Missing in GSTR-1, Tax Amount Mismatch, HSN Mismatch, etc.)
- **Export Button** — download filtered results
- **Invoice Table** with columns:
  - Invoice ID, Vendor Name, GSTIN, Taxable Amount, Tax Amount, HSN Code, Match Status, Risk Level, Period
- Each status has a color-coded badge with an icon (CheckCircle, XCircle, AlertCircle, FileWarning)
- Risk level badges: High (red), Medium (amber), Low (green)
- `formatINR()` utility for Indian number formatting (e.g., ₹4,50,000)

---

### 4.6 ITC Risk Dashboard

**File:** `src/pages/ITCRisk.jsx` (176 lines)

Analytics dashboard focused on **Input Tax Credit risk assessment**.

**Components:**
- **KPI Cards** (3 cards):
  - Total ITC at Risk (₹)
  - Average Risk Score (%)
  - High-Risk Invoices (count)
- **Bar Chart** — "Tax at Risk by Mismatch Type" showing ₹ amounts per category
- **Line Chart** — "ITC Risk Trend" over 6 months
- **Pie Chart** — "ITC Impact by Vendor" breaking down risk contribution by vendor
- **Risk Factor Table** — ML feature importance ranking (mismatch_count, total_tax_at_risk, filing_delay_days, graph_centrality, etc.)

---

### 4.7 Audit Trails Page

**File:** `src/pages/AuditTrails.jsx` (218 lines)

AI-powered **explainable audit trails** that show WHY an invoice is flagged.

**Features:**
- **Invoice List Panel** (left side):
  - Shows all mismatched invoices with vendor name, tax amount, and mismatch type
  - Search/filter functionality
  - Click an invoice to select it
- **AI Explanation Panel** (right side):
  - "Generate Audit Trail" button triggers an LLM explanation
  - **Typing Effect** animation — the explanation text appears character-by-character (speed: 12ms per char) to simulate real-time AI generation
  - **Summary** — plain-language explanation of why the invoice is flagged
  - **Evidence List** — bullet points of specific facts from the knowledge graph
  - **Recommendation** — actionable advice citing CGST Act sections
  - **Graph Path** — visual traversal path showing the invoice's journey through the knowledge graph
  - Sparkles icon and Bot icon for AI branding
  - Loading state with spinner during "generation"

**TypingEffect Component:**
- Custom component that reveals text character-by-character
- Uses `useEffect` with `setInterval` for smooth animation
- Speed configurable (default 12ms)

---

### 4.8 Vendor Compliance Page

**File:** `src/pages/VendorCompliance.jsx` (289 lines)

Comprehensive **vendor scoring and compliance analysis**.

**Components:**
- **KPI Cards** (3 cards):
  - Total Vendors (count)
  - High Risk Vendors (count)
  - Average Compliance Score (%)
- **Vendor Table** with columns:
  - Vendor Name, GSTIN, State, Risk Score (progress bar), Status badge, Total Transactions, Missed Filings, Avg Days Late
  - Sortable, filterable, searchable
  - Status badges: Compliant (green), Review (amber), High Risk (red)
- **Bar Chart** — "Top 10 Vendors by Risk Score"
- **Line Chart** — "Compliance Trend" over time
- **Radar Chart** — "Risk Factor Analysis" showing multi-dimensional risk profile
- 20 vendors in the dataset covering companies like Tata Steel, Reliance Industries, Hyderabad Steels, SunPharma, Infosys, Wipro, etc.

---

### 4.9 Settings Page

**File:** `src/pages/Settings.jsx` (408 lines)

A full **settings panel** with multiple tabs.

**Tabs:**
1. **Profile** — Edit name, email; view role and join date; save profile updates
2. **Appearance** — Theme selector (Dark/Light/System) with live preview icons, accent color options, font size slider, sidebar density
3. **Notifications** — Toggle email alerts, mismatch alerts, weekly digest, vendor risk alerts; configure alert threshold
4. **Data** — Database connection settings (Neo4j URI, database name), auto-reconciliation toggle, data retention period dropdown
5. **Security** — Change password, two-factor authentication toggle, session timeout, API key management

**Features:**
- Tabbed navigation with icons (User, Palette, Bell, Database, Shield)
- Success toast notification after saving
- Forms with various input types (text, toggle switches, sliders, dropdowns)
- Logout button in the profile tab
- All Settings persisted via state (UI-only in current version)

---

### 4.10 Theme System (Dark/Light)

**File:** `src/context/ThemeContext.jsx` (31 lines)

- Stores theme preference in localStorage (`gst-theme`)
- Default theme: **dark**
- Sets `data-theme` attribute on `<html>` element
- Toggle function switches between `dark` and `light`
- Theme toggle button in sidebar (Sun icon → Light, Moon icon → Dark)

The `index.css` file contains comprehensive CSS custom properties for both themes:
- **Dark theme**: Dark navy backgrounds (`#0a0e1a`, `#111827`), glass-morphism cards, neon accent colors
- **Light theme**: White/gray backgrounds, subtle shadows, adjusted text colors

---

### 4.11 Mock Data

**File:** `src/data/mockData.js` (249 lines, 24KB)

Comprehensive realistic mock data including:

- **`vendors`** (20 entries) — Indian companies with real-format GSTINs, states, risk scores, compliance status, transaction volumes
- **`invoices`** (20+ entries) — Invoice IDs, vendor references, taxable amounts, tax breakdowns (CGST/SGST/IGST), HSN codes, match statuses, risk levels, filing periods
- **`mismatches`** — Filtered subset of invoices where `matchStatus !== 'Matched'`
- **`mismatchTypes`** — Aggregated mismatch categories with counts, tax amounts, and chart colors
- **`itcTrend`** — Monthly ITC at-risk data (Jan–Sep 2025)
- **`gstrReturns`** — GSTR-1, GSTR-2B, GSTR-3B filing records with dates and totals
- **`riskFeatures`** — ML model feature importance values
- **`auditExplanations`** — Pre-built LLM-style explanations for 4 flagged invoices, each with:
  - Summary, Evidence array, Recommendation, Graph Path
- **`graphData`** — Knowledge graph nodes and edges for visualization:
  - 16+ nodes (vendors, invoices, GSTR returns, e-invoices, e-way bills)
  - 15+ edges (ISSUED_INVOICE, REPORTED_IN, SUMMARIZED_IN, ELECTRONIC_VERSION, COVERS_SHIPMENT)

---

### 4.12 CSS & Styling

**File:** `src/index.css` (30KB, ~1000+ lines)

A complete design system with:

- **CSS Custom Properties** for dark/light themes (50+ variables)
- **Glass-morphism** card effects with backdrop-filter blur
- **Gradient accents** on active elements and buttons
- **Typography** using Google Fonts (Inter)
- **Custom animations**: fadeIn, slideUp, pulse, shimmer
- **Responsive sidebar** with hover effects and active state indicators
- **Styled form elements**: inputs, toggles, switches, sliders, dropdowns
- **Chart container** styles with consistent padding and rounded corners
- **Table styles**: striped rows, hover effects, scrollable containers
- **Status badges**: colored pills for Compliant, Review, High Risk, Matched, etc.
- **Login page** specific styles: floating orbs, feature cards, glass panels
- **Toast notifications**: slide-in success/error messages
- **Knowledge graph** container and info panel styles
- **Sidebar user section** with avatar circle and user info
- **Settings page** tab navigation and form layouts

---

## 5. Backend — FastAPI + Python

### 5.1 main.py — API Server

**File:** `backend/main.py` (172 lines)

The main FastAPI application with CORS enabled for the React frontend.

**Key details:**
- App title: "GST ReconcileAI API"
- Version: 1.0.0
- CORS: All origins allowed (dev mode)
- Mock data: 4 vendors (V001, V005, V010, V013) and 5 mismatches
- Runs on `http://0.0.0.0:8000`

---

### 5.2 reconcile.py — Reconciliation Engine

**File:** `backend/reconcile.py` (147 lines)

A `ReconciliationEngine` class that detects GST mismatches using **Neo4j graph traversal**.

**Mismatch Detection Types:**

1. **Missing in GSTR-1** (`find_missing_invoices`) — Invoices in GSTR-2B that the vendor didn't report in GSTR-1. Uses multi-hop traversal: `GSTR-2B → Invoice → MATCHES → GSTR-1`

2. **Tax Amount Mismatch** (`find_tax_mismatches`) — Same invoice has different tax amounts in GSTR-1 vs GSTR-2B. Compares CGST + SGST values.

3. **HSN Mismatch** (`find_hsn_mismatches`) — HSN code differs between the two filings.

4. **E-Way Bill Missing** (`find_missing_ewaybills`) — Invoices above ₹50,000 threshold without an associated e-Way Bill.

**Risk Classification** (`classify_mismatch`):
- **High Risk**: Tax > ₹1,00,000 OR vendor has > 5 past mismatches
- **Medium Risk**: Tax > ₹50,000 OR vendor has > 2 past mismatches
- **Low Risk**: Everything else

**`full_reconciliation(period)`** runs all 4 checks, merges results, and sorts by financial impact.

---

### 5.3 risk_model.py — Vendor Risk ML Model

**File:** `backend/risk_model.py` (174 lines)

A `VendorRiskModel` class that trains a **RandomForest classifier** to predict vendor non-compliance.

**ML Features (8 features):**

| Feature | Description |
|---|---|
| `mismatch_count` | Number of past mismatches |
| `total_tax_at_risk` | ₹ amount of tax in disputed invoices |
| `filing_delay_days` | Average days late in filing |
| `graph_centrality` | PageRank score from knowledge graph |
| `transaction_volume` | Total number of transactions |
| `community_cluster` | Community detection cluster ID |
| `einvoice_compliance_rate` | % of invoices with valid e-Invoice |
| `state_risk_factor` | State-level risk weighting |

**Key Methods:**
- `extract_features_from_graph(driver)` — Cypher query to pull features from Neo4j + GDS
- `generate_synthetic_training_data(n=500)` — Creates realistic training data with heuristic labels
- `train()` — Trains RandomForest (100 trees, max_depth=8, balanced classes), evaluates with AUC-ROC, cross-validation
- `predict_risk()` — Returns risk probability + label (Low < 0.3, Medium 0.3–0.6, High > 0.6)
- `save()` / `get_feature_importance()` — Model persistence and interpretability

---

### 5.4 explain.py — Audit Trail Generator

**File:** `backend/explain.py` (174 lines)

Two classes for generating **explainable audit trails**:

#### `AuditTrailGenerator` (Full LangChain + GraphRAG)
- Connects to Neo4j Knowledge Graph + OpenAI GPT-4
- Uses `GraphCypherQAChain` to:
  1. Convert natural language question → Cypher query
  2. Execute query on Neo4j
  3. Feed results to GPT-4 for human-readable explanation
- Custom prompts for GST-domain expertise
- Methods: `explain_invoice()`, `explain_vendor_risk()`, `explain_itc_claim()`, `get_graph_context()`

#### `SimpleAuditTrail` (Template-based fallback)
- No LLM dependency — uses template strings
- Queries Neo4j directly and fills in explanation templates
- Handles: Missing in GSTR-1, Tax Amount Mismatch, generic statuses
- Cites CGST Act Section 16(2)(aa)

---

### 5.5 ingestion.py — Data Ingestion Pipeline

**File:** `backend/ingestion.py` (174 lines)

A `GSTIngester` class that **ETL-processes GST data** into the Neo4j Knowledge Graph.

**Supported Data Types:**

1. **GSTR-1 Ingestion** (`ingest_gstr1`) — Reads JSON, creates:
   - `Vendor` nodes (GSTIN), `Invoice` nodes (all tax fields), `GSTR` nodes
   - Relationships: `ISSUED_INVOICE`, `REPORTED_IN`

2. **GSTR-2B Ingestion** (`ingest_gstr2b`) — Reads JSON, creates:
   - Same node types + sets `itc_available` flag
   - Marks invoices as having a GSTR-2B source

3. **e-Invoice Ingestion** (`ingest_einvoice`) — Reads JSON, creates:
   - `EInvoice` nodes (IRN, acknowledgement date, status)
   - Relationship: `ELECTRONIC_VERSION`

4. **Cross-Matching** (`run_matching`) — Creates `MATCHES` relationships between invoices appearing in both GSTR-1 and GSTR-2B for a given period. Sets `match_status = 'Matched'`.

**CLI Usage:**
```bash
python ingestion.py --file gstr1_sample.json --type GSTR-1 --period 2025-07
```

---

## 6. API Endpoints

| Method | Endpoint | Parameters | Description |
|---|---|---|---|
| GET | `/` | — | Health check, returns service info |
| GET | `/api/reconcile` | `period` (optional, YYYY-MM) | Get mismatches with total tax at risk |
| GET | `/api/vendor-risk` | `vendor_id` (required) | Get vendor risk score with ML details |
| GET | `/api/explain` | `invoice` (required) | Get LLM-generated audit explanation |
| GET | `/api/graph-data` | — | Get knowledge graph nodes and edges |

**Example Responses:**

```json
// GET /api/reconcile?period=2025-07
{
  "period": "2025-07",
  "mismatch_count": 3,
  "total_tax_at_risk": 259800,
  "mismatches": [...]
}

// GET /api/vendor-risk?vendor_id=V005
{
  "vendor_id": "V005",
  "vendor_name": "Hyderabad Steels Pvt",
  "risk_score": 0.78,
  "status": "High Risk",
  "model": "RandomForestClassifier",
  "features_used": [...]
}

// GET /api/explain?invoice=INV-2025-001
{
  "invoice": "INV-2025-001",
  "explanation": {
    "summary": "Invoice INV-2025-001 ... is flagged because ...",
    "evidence": [...],
    "recommendation": "ITC of ₹81,000 at risk under Section 16(2)(aa)...",
    "graph_path": "Your Entity → GSTR-2B → INV-2025-001 → [MISSING: Vendor GSTR-1] → ..."
  }
}
```

---

## 7. How to Run

### Frontend (React + Vite)

```bash
cd "klh hackathon"
npm install
npm run dev
# → Opens on http://localhost:5173
```

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
# → Runs on http://localhost:8000
```

### Default Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@gstreconcile.ai` | `admin123` |
| Auditor | `auditor@gstreconcile.ai` | `auditor123` |

---

## 8. Key Features Summary

| # | Feature | Implementation |
|---|---|---|
| 1 | **Knowledge Graph Visualization** | Interactive force-directed graph with color-coded nodes for Vendors, Invoices, GSTR Returns, e-Invoices, e-Way Bills |
| 2 | **GST Reconciliation Engine** | Multi-hop graph traversal to detect Missing in GSTR-1, Tax Mismatches, HSN Mismatches, Missing e-Way Bills |
| 3 | **Predictive Vendor Risk Scoring** | RandomForest ML model trained on 8 graph-derived features (mismatch_count, centrality, etc.) |
| 4 | **Explainable Audit Trails** | LangChain + Neo4j GraphRAG generates natural-language explanations with evidence and CGST Act citations |
| 5 | **Data Ingestion Pipeline** | ETL for GSTR-1, GSTR-2B, and e-Invoice JSON files into Neo4j |
| 6 | **ITC Risk Analytics** | Dashboard with trend charts, type breakdowns, vendor impact analysis |
| 7 | **Vendor Compliance Scoring** | 20-vendor analysis with risk scores, compliance status, radar charts |
| 8 | **User Authentication** | Login/Signup with localStorage DB, session persistence, role-based access |
| 9 | **Dark/Light Theme** | Full theme system with CSS custom properties, persisted in localStorage |
| 10 | **Settings Panel** | Profile editing, appearance customization, notification preferences, database config, security settings |
| 11 | **Animated UI** | Framer Motion stagger animations, typing effects, smooth transitions |
| 12 | **Responsive Charts** | Chart.js with Line, Bar, Doughnut, Pie, Radar chart types |
| 13 | **Indian Formatting** | INR currency formatting (₹), realistic GSTINs, Indian company names |

---

> **Built for KLH Hackathon — February 2026**
