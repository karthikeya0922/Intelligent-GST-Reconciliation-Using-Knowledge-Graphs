# Phase 4 — GST Risk Intelligence Dashboard, End-to-End Integration & Production Hardening

## 1. Executive Summary

Phase 4 delivers the complete user-facing intelligence layer, production API endpoints, and end-to-end integration for the **Intelligent GST Reconciliation & Risk Detection System**. Built strictly upon the empirical findings and validated architectures of Phases 1–3, the Phase 4 dashboard operationalizes machine learning risk indicator scores, financial Input Tax Credit (ITC) exposure quantification, Tree SHAP factor attributions, and time-safe Knowledge Graph investigation context into a unified analyst workstation.

---

## 2. Core Architectural Tenets (Preserved Across Phases 1–4)

* **Tabular XGBoost as Primary Predictive Model:** 19 engineered tabular features with native Tree SHAP explainability.
* **Knowledge Graph as Investigation & Context Layer:** Topological context (suppliers, customers, reciprocal bilateral trading, directed trade loops) without synthetic or unvalidated graph-derived predictive feature boosts (honoring Phase 2.1 findings).
* **0–100 ML Risk Indicator Score:** Normalized continuous score reflecting model probability distribution:
  $$\text{Score} = 100 \times [0.5 \times P(\text{MEDIUM}) + 1.0 \times P(\text{HIGH})]$$
* **Decoupled ITC Financial Exposure:** Financial exposure (₹) is evaluated independently as a material monetary quantity and never conflated with fraud or statutory culpability.
* **Separation of Model Class and Operational Priority:** Model Class (`LOW`, `MEDIUM`, `HIGH`) and Operational Review Priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) remain strictly separate concepts.
* **Strict Temporal Leakage Protection:** Every feature aggregation and Knowledge Graph relationship extraction strictly obeys $t \le T_k$ (where $T_k$ is the evaluation period). Zero future relationship leakage is permitted.

---

## 3. Implemented Phase 4 Views & User Experiences

| Route | Component | Key Capabilities |
| :--- | :--- | :--- |
| `/` & `/dashboard` | `Dashboard.jsx` | 6 dynamic backend KPI cards, Risk Distribution doughnut chart, ITC exposure breakdown, 24-month longitudinal trend, interactive Risk × Exposure Prioritization Matrix. |
| `/vendors` | `VendorRiskTable.jsx` | Full portfolio directory (2,015 vendors), text search, risk band filters, priority filters, multi-field sorting, server-side pagination, quick actions to detail and investigation. |
| `/vendors/:vendor_id` | `VendorDetail.jsx` | Entity demographic profile, 0–100 score, Tree SHAP top drivers and protective factors, multi-domain auditable evidence (reconciliation, compliance, graph), chronological score evolution. |
| `/investigation` & `/investigation/:vendor_id` | `InvestigationWorkspace.jsx` | Primary auditor workstation with an 8-step sequential workflow, dossier review, interactive graph inspector, operational action recommendation, and audit JSON file export. |
| `/itc-exposure` | `ITCExposureAnalytics.jsx` | Monetary quantification of potential reconciliation exposure, portfolio totals and averages, exposure breakdown by risk class, top 15 material vendor ranking table. |
| `/graph` & `/knowledge-graph` | `KnowledgeGraphExplorer.jsx` | Time-safe interactive force-directed graph with depth 1 and depth 2 views, temporal cutoff selector ($t \le \text{period}$), counterparty concentration metrics, structural network flags. |
| `/methodology` | `Methodology.jsx` | Comprehensive research specifications: benchmark characteristics, Tabular XGBoost walk-forward validation, Phase 2.1 neutral finding documentation, and governance limitations. |

---

## 4. Key Metrics from Benchmark Validation (Period 2026-02)

* **Total Active Vendors:** 2,015
* **Portfolio Invoices:** 168,213 across 24 calendar months
* **Cumulative ITC Exposure:** ₹26,871,137.88 (₹2.69 Cr)
* **Average ITC Exposure per Vendor:** ₹13,335.55
* **Model Class Breakdown:** LOW: 1,420 (70.47%), MEDIUM: 370 (18.36%), HIGH: 225 (11.17%)
* **Operational Priority Breakdown:** LOW: 1,382, MEDIUM: 337, HIGH: 254, CRITICAL: 42
