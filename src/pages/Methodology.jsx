import React from 'react';
import {
  FileCode,
  Database,
  Cpu,
  ShieldAlert,
  Network,
  AlertTriangle,
  Layers,
  Scale,
  CheckCircle2,
  BookOpen
} from 'lucide-react';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

export default function Methodology() {
  return (
    <div className="methodology-page">
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>📚 Research Methodology & Architecture Specification</h2>
            <p>Empirical Foundations, Predictive Modeling, Knowledge Graph Context & Validation Standards</p>
          </div>
        </div>
      </div>

      <ResearchDisclaimer />

      {/* Overview Grid */}
      <div className="grid grid-2 gap-4 mb-4">
        {/* Dataset Specification */}
        <div className="card">
          <div className="card-header flex items-center gap-2 justify-start">
            <Database size={18} className="text-accent" />
            <h3>1. Controlled Hybrid Research Benchmark</h3>
          </div>
          <p className="text-xs text-muted mb-3">
            Designed to simulate realistic GST tax ecosystems with high fidelity while protecting sensitive taxpayer information.
          </p>

          <div className="flex flex-col gap-2 text-xs">
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Simulated Entities:</span>
              <strong>2,015 registered vendors</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Invoice Population:</span>
              <strong>168,213 individual invoices</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Temporal Horizon:</span>
              <strong>24 simulated calendar months (2024-04 to 2026-02)</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Panel Observations:</span>
              <strong>46,345 vendor-period feature observations</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted">Ecosystem Topologies:</span>
              <span>8 behavioral vendor archetypes (Profiles A–H)</span>
            </div>
          </div>
        </div>

        {/* Predictive Model Architecture */}
        <div className="card">
          <div className="card-header flex items-center gap-2 justify-start">
            <Cpu size={18} className="text-accent" />
            <h3>2. Primary Predictive ML Architecture</h3>
          </div>
          <p className="text-xs text-muted mb-3">
            Validated tabular gradient boosting algorithm trained under strict temporal separation.
          </p>

          <div className="flex flex-col gap-2 text-xs">
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Model Type:</span>
              <strong>Tabular XGBoost Classifier</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Feature Space:</span>
              <strong>19 engineered tabular features</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Split Protocol:</span>
              <strong>Strict Temporal Walk-Forward Split (train &lt; val &lt; test)</strong>
            </div>
            <div className="flex justify-between py-1 border-bottom">
              <span className="text-muted">Explainability Engine:</span>
              <strong>Native Tree SHAP (Exact Additive Feature Attributions)</strong>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-muted">Stability Benchmark:</span>
              <span>Validated across 5 independent seeds (seeds 42, 101, 202, 303, 404)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Phase 2.1 Empirical Finding (Mandatory Spec) */}
      <div className="card mb-4" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
        <div className="card-header flex items-center gap-2 justify-start">
          <Scale size={18} className="text-accent" />
          <h3>3. Phase 2.1 Empirical Finding: Knowledge Graph Feature Role</h3>
        </div>
        <div className="p-2">
          <div className="p-3 border rounded mb-3" style={{ background: 'rgba(245, 158, 11, 0.06)', borderColor: 'rgba(245, 158, 11, 0.25)' }}>
            <p className="font-semibold text-sm text-warning mb-1">
              Statistically Insignificant Graph Predictive Gain:
            </p>
            <p className="text-xs text-secondary leading-relaxed mb-0">
              "Knowledge Graph-derived predictive features did not produce statistically significant incremental improvement over the tabular XGBoost baseline on the benchmark."
            </p>
          </div>

          <p className="text-xs text-secondary leading-relaxed">
            In comprehensive Phase 2.1 5-seed validation experiments, augmenting the 19-feature tabular XGBoost model with graph centrality, PageRank, and community features yielded a delta of only +0.003 in macro-F1 (p-value &gt; 0.05). Consequently, the Knowledge Graph is preserved as an <strong>investigation, evidence-aggregation, and topological context layer</strong> rather than an artificial predictive feature booster.
          </p>
        </div>
      </div>

      {/* Risk Framework & Separation */}
      <div className="card mb-4">
        <div className="card-header flex items-center gap-2 justify-start">
          <ShieldAlert size={18} className="text-accent" />
          <h3>4. Conceptual Separation: Risk Score vs. Exposure vs. Priority</h3>
        </div>
        <div className="grid grid-3 gap-3 text-xs mt-2">
          <div className="p-3 border rounded">
            <h4 className="font-bold text-sm text-warning mb-1">0–100 ML Risk Score</h4>
            <p className="text-muted leading-relaxed">
              Continuous indicator computed from model class probabilities:
              <br />
              <code>Score = 100 × [0.5 × P(MED) + 1.0 × P(HIGH)]</code>
              <br />
              Represents model uncertainty and estimated compliance risk likelihood.
            </p>
          </div>

          <div className="p-3 border rounded">
            <h4 className="font-bold text-sm text-info mb-1">Financial ITC Exposure</h4>
            <p className="text-muted leading-relaxed">
              Monetary quantity reflecting the cumulative value of reconciliation discrepancies, missing filings, or timing gaps.
              Decoupled from fraud determination.
            </p>
          </div>

          <div className="p-3 border rounded">
            <h4 className="font-bold text-sm text-danger mb-1">Operational Priority</h4>
            <p className="text-muted leading-relaxed">
              Business triage matrix (LOW, MEDIUM, HIGH, CRITICAL) combining Risk Band and Financial Exposure magnitude to recommend proportionate audit interventions.
            </p>
          </div>
        </div>
      </div>

      {/* Research Limitations & Guardrails */}
      <div className="card mb-4">
        <div className="card-header flex items-center gap-2 justify-start">
          <AlertTriangle size={18} className="text-warning" />
          <h3>5. Research Limitations & Governance Guardrails</h3>
        </div>
        <div className="text-xs text-secondary flex flex-col gap-2">
          <div className="flex items-start gap-2">
            <CheckCircle2 size={14} className="text-accent mt-0.5" />
            <span>
              <strong>Controlled Benchmark Constraints:</strong> Results reflect simulated economic patterns and synthetic invoice distributions. Model behavior must be independently re-calibrated prior to operational enterprise deployment.
            </span>
          </div>

          <div className="flex items-start gap-2">
            <CheckCircle2 size={14} className="text-accent mt-0.5" />
            <span>
              <strong>No Statutory Adjudication:</strong> The system acts strictly as an investigative triage assistant and does not verify statutory non-compliance, legal culpability, or tax liability.
            </span>
          </div>

          <div className="flex items-start gap-2">
            <CheckCircle2 size={14} className="text-accent mt-0.5" />
            <span>
              <strong>Temporal Causality Protection:</strong> All feature aggregations and network relationship extractions strictly observe <code>t ≤ T_k</code> to prevent forward-looking data leakage.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
