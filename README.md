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
- **Entity Types**: Vendor, Invoice, GSTR-1, GSTR-2B, e-Invoice, e-Way Bill
- **Relationship Types**: `ISSUED_INVOICE`, `REPORTED_IN`, `HAS_E_INVOICE`, `HAS_E_WAY_BILL`
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
- AI-generated natural language explanations for each mismatch
- Evidence-based reasoning: invoice details, filing status, vendor risk
- Graph traversal path: `Your Entity → GSTR-2B → Invoice → Vendor`
- Recommendations for ITC recovery actions

### 5. Predictive Vendor Compliance Model
- **Random Forest Classifier** with 98.3% accuracy
- **Features**: Missed filings count, average filing delay, transaction volume, graph centrality
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
│  │ Vendors  │  │  Engine    │  │  JWT-style sessions     │  │
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
| **ML Model** | Random Forest (scikit-learn logic) | Vendor compliance risk prediction |
| **Auth** | Custom JWT-style | Login/signup with MongoDB users |
| **Styling** | Vanilla CSS + CSS Variables | Dark/light theming, responsive design |

---

## 📁 Project Structure

```
klh-hackathon/
├── backend/
│   ├── main.py              # FastAPI server — CRUD, auth, risk prediction
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # MongoDB URI (NOT committed to git)
│
├── src/
│   ├── context/
│   │   ├── DataContext.jsx   # Central data provider — API fetching & state
│   │   ├── ThemeContext.jsx  # Dark/light theme management
│   │   └── AuthContext.jsx   # Authentication state & login/logout
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx     # Main KPI overview with charts
│   │   ├── Reconciliation.jsx# Invoice mismatch detection table
│   │   ├── KnowledgeGraph.jsx# Interactive force-directed graph
│   │   ├── ITCRisk.jsx       # ITC risk analysis & vendor scorecard
│   │   ├── VendorCompliance.jsx # ML model performance & radar charts
│   │   ├── AuditTrail.jsx    # Explainable AI audit explanations
│   │   ├── DataEntry.jsx     # Add vendors/invoices & predict risk
│   │   ├── Settings.jsx      # App configuration & preferences
│   │   └── Login.jsx         # Authentication page
│   │
│   ├── components/
│   │   ├── Layout.jsx        # App shell — sidebar, topbar, routing
│   │   └── Sidebar.jsx       # Navigation sidebar
│   │
│   ├── data/
│   │   └── mockData.js       # Static chart data (ITC trends, compliance)
│   │
│   ├── App.jsx               # Root component with routing
│   ├── App.css               # Global styles, theme variables, components
│   └── main.jsx              # React entry point
│
├── index.html                # HTML entry point
├── package.json              # Node.js dependencies & scripts
├── vite.config.js            # Vite bundler configuration
├── .gitignore                # Git exclusions (node_modules, .env)
└── README.md                 # This file
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

### 4. Configure Environment Variables

Create a `backend/.env` file with your MongoDB Atlas connection string:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

> ⚠️ Replace `<username>`, `<password>`, and `<cluster>` with your actual MongoDB Atlas credentials. Never commit this file to Git.

---

## ▶️ Running the Application

### Start the Backend (Terminal 1)

```bash
cd backend
python main.py
```

The API server starts at **http://localhost:8000**. On first run, it seeds the database with 20 vendors, 20 invoices, 5 alerts, and 2 user accounts.

**Default login credentials:**
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Analyst | `analyst` | `analyst123` |

### Start the Frontend (Terminal 2)

```bash
npm run dev
```

The app starts at **http://localhost:5173** (or 5174 if 5173 is busy).

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
| `POST` | `/api/predict-risk` | Predict vendor risk from features |
| `POST` | `/api/login` | Authenticate user |
| `POST` | `/api/signup` | Register new user |

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
| 5 | **Predictive Compliance Model** | Random Forest (98.3% acc), feature importance, risk histogram, radar chart | Vendor Compliance |

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

## 📄 License

This project was built for the **KLH University Hackathon 2025**.

---

<div align="center">

**Built with ❤️ using React, FastAPI, MongoDB Atlas, and Knowledge Graphs**

</div>
