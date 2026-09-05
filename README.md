# 🧠 Intelligent GST Reconciliation Using Knowledge Graphs

> **AI-Powered GST Invoice Reconciliation System** — A full-stack web application that uses Knowledge Graphs, Machine Learning (Random Forest), and Graph-based Anomaly Detection to automate GSTR-1 vs GSTR-2B reconciliation, predict vendor compliance risk, and provide explainable audit trails.

![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4.x-FF6384?logo=chartdotjs&logoColor=white)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Deliverables](#deliverables)
- [Screenshots](#screenshots)
- [Team](#team)

---

## 🎯 Overview

India's GST system requires businesses to reconcile invoices across multiple returns (GSTR-1, GSTR-2B, GSTR-3B). Mismatches lead to **blocked Input Tax Credit (ITC)** worth crores. This project builds an **intelligent reconciliation engine** that:

1. **Models GST entities** (vendors, invoices, returns) as a **Knowledge Graph**
2. **Detects mismatches** using graph traversal algorithms
3. **Predicts vendor compliance risk** using a **Random Forest classifier**
4. **Generates explainable audit trails** with graph-path evidence
5. **Provides an interactive dashboard** for real-time monitoring

### Problem Statement

| Challenge | Our Solution |
|---|---|
| Manual invoice matching is error-prone | Automated graph-based reconciliation |
| Hard to identify risky vendors | ML-powered vendor risk scoring |
| Audit trails lack transparency | Graph-path explainable AI |
| Static reports, no real-time updates | Dynamic dashboard with live MongoDB data |
| Scattered data across returns | Unified Knowledge Graph data model |

---

## ✨ Key Features

### 1. Knowledge Graph Schema & Data Model
- **Entity Types**: Taxpayer, Vendor, Invoice, GSTR-1, GSTR-2B, GSTR-3B, e-Invoice, e-Way Bill
- **Relationship Types**: `ISSUED_INVOICE`, `REPORTED_IN`, `BILLED_TO`, `RECORDED_IN_PR`,
  `FILED_RETURN`, `ELECTRONIC_VERSION`, `COVERS_SHIPMENT`
- Interactive Force-Directed Graph visualization with layer toggles
- Click-to-explore node details with risk scores and connections

### 2. Reconciliation Engine
- Automated GSTR-1 ↔ GSTR-2B matching with mismatch classification
- Mismatch types: Missing in GSTR-1, Tax Amount Mismatch, HSN Mismatch, Late Filing, E-Way Bill Missing
- Filterable reconciliation table with period, risk, and type filters
- Cypher-style graph traversal path display for each mismatch

### 3. ITC Risk Dashboard
- Real-time At-Risk ITC calculation from mismatched invoices
- Vendor risk distribution (Compliant / Review / High Risk)
- Top vendors by at-risk ITC horizontal bar chart
- ITC Blocked trend line chart
- Full vendor compliance scorecard with risk bars

### 4. Explainable Audit Trails
- Generated for **every** flagged invoice from live graph facts (`GET /api/audit-trail/{id}`)
- Each evidence line traces to a present or absent relationship, so the explanation
  cannot drift from the data
- Cites the applicable CGST provision — s.16(2)(aa) for an unreported invoice,
  s.16(2)(c) where tax was never remitted, s.35(1) for an unbooked purchase
- Findings are ranked by gravity, so the headline reports the most serious issue
  rather than whichever label happened to be stored
- Prints the traversal that produced it, including the second hop through the
  supplier's GSTR-3B and the taxpayer's Purchase Register

### 5. Predictive Vendor Compliance Model
- **Random Forest Classifier** (300 trees, depth 8) served from the API — held-out accuracy **76.8%**, ROC-AUC **0.853**, 5-fold CV **76.8%**
- Trained on a synthetic vendor population with *stochastic* labels, so the score reflects real generalisation rather than a model re-learning its own labelling rule
- **8 features**: mismatch count, tax at risk, filing delay, graph centrality, transaction volume, community cluster, e-invoice compliance rate, state risk factor
- Falls back to a documented weighted-sum heuristic if scikit-learn is unavailable — the API reports which one scored each request
- Risk score histogram showing vendor distribution
- Radar chart for multi-dimensional vendor compliance profile
- Real-time prediction via Data Entry page

### 6. Dynamic Data Entry
- Add new vendors with automatic risk prediction
- Add new invoices with automatic mismatch detection
- All changes persist to **MongoDB Atlas** (cloud)
- All dashboards update in real-time after data entry

### 7. Authentication & Settings
- Login/Signup with MongoDB-backed user management
- Configurable settings: notifications, reconciliation rules, display preferences
- Dark/Light theme toggle

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌────────────┐  │
│  │Dashboard │ │Reconcile   │ │Knowledge  │ │Data Entry  │  │
│  │  (KPIs)  │ │  Engine    │ │  Graph    │ │& Prediction│  │
│  └────┬─────┘ └─────┬──────┘ └─────┬─────┘ └──────┬─────┘  │
│       │             │              │               │        │
│  ┌────▼─────────────▼──────────────▼───────────────▼─────┐  │
│  │              DataContext (React Context API)           │  │
│  │        fetchAll() ←→ addVendor() ←→ addInvoice()      │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │ REST API (HTTP)
┌──────────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI + Python)                  │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │ CRUD API │  │Risk Predict│  │  Auth (Login/Signup)    │  │
│  │ Vendors  │  │  Engine    │  │  bcrypt password hashes │  │
│  │ Invoices │  │(RandomForest│  │                         │  │
│  │ Alerts   │  │  Features) │  │                         │  │
│  └────┬─────┘  └─────┬──────┘  └────────┬────────────────┘  │
│       │              │                   │                   │
│  ┌────▼──────────────▼───────────────────▼───────────────┐  │
│  │              PyMongo Driver                           │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │ MongoDB Wire Protocol
┌──────────────────────────▼──────────────────────────────────┐
│              MongoDB Atlas (Cloud Database)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ vendors  │ │ invoices │ │  alerts  │ │  users   │       │
│  │ (20+)    │ │  (20+)   │ │   (5+)   │ │   (2+)   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18 + Vite | SPA with hot module replacement |
| **UI Components** | Framer Motion | Smooth page transitions & animations |
| **Charts** | Chart.js + react-chartjs-2 | KPI visualizations, histograms, radar |
| **Graph Viz** | react-force-graph-2d | Interactive knowledge graph rendering |
| **State Management** | React Context API | Centralized data with useMemo optimization |
| **Backend** | FastAPI (Python) | High-performance async REST API |
| **Database** | MongoDB Atlas (Cloud) | Document store for vendors, invoices, alerts |
| **Knowledge Graph** | Neo4j 5 (optional) | Graph-traversal reconciliation over GSTR filings |
| **ML Model** | scikit-learn RandomForestClassifier | Vendor compliance risk prediction, served from the API |
| **Auth** | bcrypt-hashed credentials in MongoDB | Login/signup; no plaintext passwords stored |
| **Styling** | Vanilla CSS + CSS Variables | Dark/light theming, responsive design |

---

## 📁 Project Structure

```
Intelligent-GST-Reconciliation-Using-Knowledge-Graphs/
├── backend/
│   ├── main.py               # FastAPI server — CRUD, auth, risk, graph endpoints
│   ├── auth_utils.py         # bcrypt hashing, validation, plaintext migration
│   ├── risk_model.py         # RandomForest vendor risk model (trained + served)
│   ├── graph_sync.py         # MongoDB → Neo4j projection
│   ├── reconcile.py          # Cypher graph-traversal reconciliation engine
│   ├── ingestion.py          # ETL for real GSTR-1/2B/e-Invoice JSON → Neo4j
│   ├── explain.py            # LangChain + Neo4j GraphRAG audit trails (optional)
│   ├── verify_graph.py       # End-to-end check of the Neo4j path
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # MONGODB_URI / NEO4J_* (NOT committed to git)
│
├── src/
│   ├── context/
│   │   ├── DataContext.jsx   # Central data provider — API fetching & derived state
│   │   ├── ThemeContext.jsx  # Dark/light theme management
│   │   └── AuthContext.jsx   # API-backed auth with offline fallback
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx     # Main KPI overview with charts
│   │   ├── Reconciliation.jsx# Mismatch table + graph traversal engine panel
│   │   ├── KnowledgeGraph.jsx# Interactive force-directed graph
│   │   ├── ITCRisk.jsx       # ITC risk analysis & vendor scorecard
│   │   ├── VendorCompliance.jsx # ML model performance & radar charts
│   │   ├── AuditTrails.jsx   # Explainable audit explanations
│   │   ├── DataEntry.jsx     # Add vendors/invoices & predict risk
│   │   ├── Settings.jsx      # App configuration & preferences
│   │   └── LoginPage.jsx     # Authentication page
│   │
│   ├── data/
│   │   └── mockData.js       # Offline fallback dataset + static chart series
│   │
│   ├── App.jsx               # Root component — sidebar, routing, live status
│   ├── App.css               # Layout overrides
│   ├── index.css             # Design system — theme variables, components
│   └── main.jsx              # React entry point
│
├── docker-compose.yml        # Neo4j + MongoDB for local development
├── eslint.config.js          # ESLint configuration
├── GST_ReconcileAI_Comprehensive_Report.pdf # Comprehensive project report
├── index.html                # HTML entry point
├── package-lock.json         # Locked npm dependencies
├── package.json              # Node.js dependencies & scripts
├── run_all.ps1               # PowerShell launcher script
├── start_app.bat             # Batch launcher script
├── total.md                  # Comprehensive technical documentation
├── vite.config.js            # Vite bundler configuration
└── README.md                 # Project documentation
```

---

## 🚀 Setup & Installation

### Prerequisites

- **Node.js** ≥ 18.x ([download](https://nodejs.org/))
- **Python** ≥ 3.10 ([download](https://www.python.org/))
- **MongoDB Atlas** account (free tier works) — [cloud.mongodb.com](https://cloud.mongodb.com)

### 1. Clone the Repository

```bash
git clone https://github.com/karthikeya0922/Intelligent-GST-Reconciliation-Using-Knowledge-Graphs.git
cd Intelligent-GST-Reconciliation-Using-Knowledge-Graphs
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Databases

The quickest path is Docker, which brings up both MongoDB and Neo4j:

```bash
docker compose up -d
```

| Service | URL | Credentials |
|---|---|---|
| Neo4j Browser | http://localhost:7474 | `neo4j` / `gstreconcile` |
| Neo4j Bolt | bolt://localhost:7687 | `neo4j` / `gstreconcile` |
| MongoDB | mongodb://localhost:27017 | none |

#### Without Docker (Windows)

Neo4j 5 needs **JDK 17 or 21** — it will not start on JDK 23/25. Portable setup,
no installer and no admin rights:

```bash
# 1. JDK 21 (skip if you already have 17 or 21)
curl -L -o jdk21.zip "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.5%2B11/OpenJDK21U-jdk_x64_windows_hotspot_21.0.5_11.zip"
unzip -q jdk21.zip -d C:/neo4j

# 2. Neo4j Community Server
curl -L -o neo4j.zip "https://dist.neo4j.org/neo4j-community-5.26.0-windows.zip"
unzip -q neo4j.zip -d C:/neo4j
```

Then, in PowerShell:

```powershell
$env:JAVA_HOME = "C:
eo4j\jdk-21.0.5+11"
cd C:
eo4j
eo4j-community-5.26.0
.in
eo4j-admin.bat dbms set-initial-password gstreconcile   # once, before first start
.in
eo4j.bat console
```

MongoDB can likewise be installed directly from
[mongodb.com/try/download/community](https://www.mongodb.com/try/download/community).

---

Both are **optional**. The app degrades gracefully:

- **No MongoDB** → the frontend serves its bundled mock dataset
- **No Neo4j** → graph endpoints report offline and reconciliation falls back to
  MongoDB label matching. The sidebar shows the real state of each subsystem, so
  you can always see which engine produced a result.

### 5. Configure Environment Variables

Create a `backend/.env` file:

```env
# MongoDB — local Docker, or an Atlas connection string
MONGODB_URI=mongodb://localhost:27017

# Neo4j — matches docker-compose.yml
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=gstreconcile
```

For MongoDB Atlas instead of local Docker:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

> ⚠️ Never commit private credentials or secrets to Git.

---

## ▶️ Running the Application

### Start the Backend (Terminal 1)

```bash
cd backend
python main.py
```

The API server starts at **http://localhost:8000**. On first run it:

1. Seeds MongoDB with 20 vendors, 20 invoices, 5 alerts and 2 user accounts
2. Migrates any legacy plaintext passwords to bcrypt
3. Trains and persists the vendor risk model to `backend/vendor_risk_model.pkl`
   (a few seconds; subsequent boots load it from disk)

Check what actually came up:

```bash
curl http://localhost:8000/            # subsystem summary
curl http://localhost:8000/api/model/info    # real model metrics
curl http://localhost:8000/api/graph/status  # Neo4j connectivity
```

**Default login credentials:**
| Role | Email | Password |
|---|---|---|
| Admin | `admin@gstreconcile.ai` | `admin123` |
| Auditor | `auditor@gstreconcile.ai` | `auditor123` |

These are hashed with bcrypt on first boot. Any plaintext passwords left by an
earlier version are migrated automatically at startup.

### Start the Frontend (Terminal 2)

```bash
npm run dev
```

The app starts at **http://localhost:5173** (or 5174 if 5173 is busy).

### Populate the Knowledge Graph (optional)

With Neo4j running, project the MongoDB data into it and verify the graph engine
end to end:

```bash
cd backend
python verify_graph.py
```

This syncs Mongo → Neo4j, runs the Cypher reconciliation, and cross-checks its
structural findings against MongoDB's own labels. You can also do the sync from
the UI — **Reconciliation → Sync Graph**, then **Run Reconciliation**. The result
panel reports which engine ran (`neo4j-graph-traversal` or `mongodb-fallback`).

---

## 🔗 The Multi-Hop ITC Chain

A flat GSTR-1 vs GSTR-2B table match answers one question: *did the supplier
report the invoice?* Reporting is not payment. The graph asks the second question
too, by traversing through the supplier to the return where tax is actually paid:

```
(Vendor)-[:ISSUED_INVOICE]->(Invoice)-[:REPORTED_IN]->(GSTR-1)     declared
(Vendor)-[:FILED_RETURN]->(GSTR3B {filed: false})                  but never paid
```

An invoice on that path looks clean one hop out and fails on the second. This is
`Supplier GSTR-3B Not Filed` — ITC blocked under **s.16(2)(c)**, invisible to
table matching.

The Purchase Register closes the loop on the buyer's side, in both directions:

| Finding | Meaning |
|---|---|
| In GSTR-2B, no `:RECORDED_IN_PR` edge | Supplier declared a supply the books never recorded — unbooked liability, or an invoice raised against your GSTIN |
| In the PR, absent from GSTR-2B | Purchase booked but no credit available — reverse any ITC taken |

---

## 🔍 How the Reconciliation Engine Classifies Findings

Each finding carries a `detection` field, because not every check is equally
graph-native:

| Detection | Meaning | Examples |
|---|---|---|
| `structural` | Derived purely from the shape of the graph — an absent edge. This is what the knowledge graph genuinely buys you. | Missing in GSTR-1, E-Way Bill Missing, e-Invoice Missing |
| `field-level` | Compares the supplier's filing against the buyer's copy of the same invoice. Requires the dual-source ingestion path (`ingestion.py`). | Tax Amount Mismatch, HSN Mismatch |
| `label-carried` | The mismatch was determined upstream and is carried on the record. Used when the graph is projected from the single-source MongoDB store. | Any type, when running the Mongo fallback |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vendors` | List all vendors with risk scores |
| `POST` | `/api/vendors` | Add vendor + auto risk prediction |
| `GET` | `/api/invoices` | List all invoices with match status |
| `POST` | `/api/invoices` | Add invoice + auto mismatch detection |
| `GET` | `/api/alerts` | List system alerts |
| `GET` | `/api/stats` | Dashboard KPI aggregations |
| `POST` | `/api/predict-risk` | Score a vendor with the RandomForest; returns the feature vector and its drivers |
| `GET` | `/api/model/info` | Which model is serving, with its real held-out metrics |
| `GET` | `/api/graph/status` | Neo4j connectivity, node and relationship counts |
| `POST` | `/api/graph/sync` | Project the MongoDB contents into Neo4j |
| `GET` | `/api/reconcile` | Graph-traversal reconciliation (`?period=2025-08`), Mongo fallback |
| `GET` | `/api/reconcile/evidence/{id}` | Graph neighbourhood backing a flagged invoice |
| `GET` | `/api/audit-trail/{id}` | Generated audit trail for any flagged invoice |
| `POST` | `/api/login` | Authenticate against bcrypt-hashed credentials |
| `POST` | `/api/signup` | Register a new user (password hashed on write) |
| `POST` | `/api/profile` | Update display name / email |
| `POST` | `/api/change-password` | Change password, verifying the current one |

### Example: Add a Vendor

```bash
curl -X POST http://localhost:8000/api/vendors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corp",
    "gstin": "29ABCDE1234F1Z5",
    "state": "Karnataka",
    "totalTransactions": 50,
    "missedFilings": 3,
    "avgDaysLate": 8
  }'
```

**Response:**
```json
{
  "vendor": {
    "id": "V021",
    "name": "Test Corp",
    "riskScore": 0.62,
    "status": "High Risk"
  }
}
```

---

## 📊 Deliverables

This project addresses **5 core deliverables** for the GST Reconciliation hackathon:

| # | Deliverable | Implementation | Page |
|---|---|---|---|
| 1 | **Knowledge Graph Schema & Data Model** | Force-directed graph with 5 entity types, 6 relationship types, layer toggles | Knowledge Graph |
| 2 | **Graph-Traversal Reconciliation** | Automated GSTR-1 ↔ GSTR-2B matching, mismatch classification, Cypher paths | Reconciliation |
| 3 | **ITC Risk Scoring** | Real-time at-risk ITC calculation, vendor scoring, distribution charts | ITC Risk Dashboard |
| 4 | **Explainable Audit Trails** | NLP-style summaries, evidence lists, graph paths, recommendations | Audit Trail |
| 5 | **Predictive Compliance Model** | Random Forest (76.8% held-out acc, 0.853 AUC), feature importance, risk histogram, radar chart | Vendor Compliance |

---

## 🖼️ Screenshots

> Navigate to `http://localhost:5173` after starting both servers to see the live application.

| Page | Description |
|---|---|
| **Dashboard** | 6 KPI cards, ITC trend line, mismatch donut, compliance bar chart, alerts |
| **Reconciliation** | Filterable invoice table with match status, risk levels, Cypher path detail |
| **Knowledge Graph** | Interactive force graph with vendor/invoice/GSTR nodes, layer toggles, zoom |
| **ITC Risk** | At-risk ITC totals, top vendors bar chart, risk pie, vendor scorecard table |
| **Vendor Compliance** | ML model metrics, feature importance, risk histogram, radar profile |
| **Audit Trail** | Expandable audit cards with AI explanations, evidence, graph paths |
| **Data Entry** | Add invoice/vendor forms, real-time risk prediction, MongoDB persistence |

---

## 👥 Team

| Name | Role |
|---|---|
| **Karthikeya** | Full-Stack Developer & ML Engineer |


---

<div align="center">

</div>
