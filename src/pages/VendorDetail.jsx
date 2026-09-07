import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  FileSearch,
  Network,
  ArrowLeft,
  DollarSign,
  Activity,
  Layers,
  CheckCircle2,
  AlertTriangle,
  History,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { getVendor, getVendorHistory } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

export default function VendorDetail() {
  const { vendor_id } = useParams();
  const navigate = useNavigate();

  const [assessment, setAssessment] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [assessRes, histRes] = await Promise.all([
          getVendor(vendor_id),
          getVendorHistory(vendor_id),
        ]);
        setAssessment(assessRes);
        setHistoryData(histRes);
      } catch (err) {
        console.error('Failed to load vendor details:', err);
        setError(err.message || `Unable to load vendor records for '${vendor_id}'.`);
      } finally {
        setLoading(false);
      }
    }

    if (vendor_id) {
      fetchData();
    }
  }, [vendor_id]);

  // Historical Risk Score Chart
  const historyChartData = useMemo(() => {
    if (!historyData?.history || historyData.history.length === 0) return null;
    const sorted = [...historyData.history].sort((a, b) => (a.period > b.period ? 1 : -1));
    return {
      labels: sorted.map((h) => h.period),
      datasets: [
        {
          label: '0–100 ML Risk Indicator Score',
          data: sorted.map((h) => h.risk_score),
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: sorted.map((h) => (h.risk_score > 66 ? '#ef4444' : h.risk_score > 33 ? '#f59e0b' : '#22c55e')),
        },
      ],
    };
  }, [historyData]);

  if (loading) {
    return (
      <div className="state-container state-loading">
        <div className="spinner" />
        <h3>Loading Vendor Profile...</h3>
        <p className="text-muted">Evaluating XGBoost prediction, Tree SHAP explanations, and historical transitions</p>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="state-container state-error">
        <AlertCircle size={42} className="error-icon" />
        <h3>Vendor Record Error</h3>
        <p className="text-muted">{error || 'Vendor not found in benchmark records.'}</p>
        <button className="btn-outline mt-2 flex items-center gap-1" onClick={() => navigate('/vendors')}>
          <ArrowLeft size={14} /> Return to Vendor Directory
        </button>
      </div>
    );
  }

  const risk = assessment.risk || {};
  const itc = assessment.itc || {};
  const evidence = assessment.evidence || {};
  const rec = assessment.recommendations || {};
  const shapFactors = assessment.explanation?.top_contributing_factors || [];
  const protectiveFactors = assessment.explanation?.protective_factors || [];

  return (
    <div className="vendor-detail-page">
      {/* Header Navigation */}
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link to="/vendors" className="text-muted text-xs flex items-center gap-1 hover-text-accent">
                <ArrowLeft size={12} /> Back to Vendor Directory
              </Link>
            </div>
            <h2>🏢 Vendor Profile: {assessment.vendor_id}</h2>
            <p className="text-xs text-muted">
              Benchmark Observation Period: <strong>{assessment.prediction_period}</strong> (Temporal Cutoff Strictly Enforced)
            </p>
          </div>

          <div className="flex gap-2">
            <button
              className="btn-outline flex items-center gap-1"
              onClick={() => navigate(`/graph?vendor=${assessment.vendor_id}`)}
            >
              <Network size={14} /> Knowledge Graph
            </button>
            <button
              className="btn-primary flex items-center gap-1"
              onClick={() => navigate(`/investigation/${assessment.vendor_id}`)}
            >
              <FileSearch size={14} /> Start Investigation
            </button>
          </div>
        </div>
      </div>

      <ResearchDisclaimer compact />

      {/* Primary KPI Header Cards */}
      <div className="kpi-grid mb-4">
        {/* ML Risk Class */}
        <div className="kpi-card">
          <div className="kpi-label">ML Model Class</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`badge-${risk.model_class?.toLowerCase() || 'low'}`}>
              {risk.model_class || 'LOW'}
            </span>
          </div>
          <div className="kpi-subtext mt-1">
            P(LOW): {(risk.probabilities?.LOW * 100).toFixed(1)}% • P(MED): {(risk.probabilities?.MEDIUM * 100).toFixed(1)}% • P(HIGH): {(risk.probabilities?.HIGH * 100).toFixed(1)}%
          </div>
        </div>

        {/* 0-100 Score */}
        <div className="kpi-card">
          <div className="kpi-label">0–100 ML Risk Score</div>
          <div className="kpi-value orange flex items-baseline gap-2">
            <span>{risk.score?.toFixed(1) || '0.0'}</span>
            <span className="text-xs font-normal text-muted">/ 100</span>
          </div>
          <div className="kpi-subtext">Presentation Band: <strong>{risk.risk_band}</strong></div>
        </div>

        {/* Financial ITC Exposure */}
        <div className="kpi-card">
          <div className="kpi-label">Financial ITC Exposure</div>
          <div className="kpi-value red">{formatINR(itc.exposure)}</div>
          <div className="kpi-subtext">Exposure Ratio: {(itc.exposure_ratio * 100).toFixed(1)}% of total tax</div>
        </div>

        {/* Operational Review Priority */}
        <div className="kpi-card">
          <div className="kpi-label">Operational Review Priority</div>
          <div className="mt-1">
            <span className={`badge-${rec.review_priority?.toLowerCase() || 'low'}`}>
              {rec.review_priority || 'ROUTINE'}
            </span>
          </div>
          <div className="kpi-subtext mt-1">{rec.recommended_action}</div>
        </div>
      </div>

      {/* Operational Priority Detail Banner */}
      <div className="card mb-4" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
        <div className="flex items-start gap-3">
          <ShieldAlert size={20} className="text-accent mt-1" />
          <div>
            <h4>Operational Decision Recommendation: {rec.recommended_action}</h4>
            <p className="text-sm text-muted mt-1">{rec.review_details}</p>
          </div>
        </div>
      </div>

      {/* Tree SHAP Explainability & Contributing Factors */}
      <div className="grid grid-2 gap-3 mb-4">
        {/* Risk Factors */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3>📈 Top Model Contributing Factors (Tree SHAP)</h3>
            <span className="text-xs text-muted">Positive Attribution</span>
          </div>
          <p className="text-xs text-muted mb-3">
            Features that contributed upward pressure to the model risk score for this evaluation period.
          </p>

          {shapFactors.length === 0 ? (
            <div className="p-3 text-center text-xs text-muted">No material upward risk factors detected.</div>
          ) : (
            <div className="flex flex-col gap-2">
              {shapFactors.map((f, idx) => (
                <div key={idx} className="p-2 border rounded" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span>{f.feature}</span>
                    <span className="text-danger">Impact: +{f.shap_value?.toFixed(3)}</span>
                  </div>
                  <div className="text-xs text-muted">{f.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Protective Factors */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3>🛡️ Protective Factors & Compliance Strengths</h3>
            <span className="text-xs text-muted">Negative Attribution</span>
          </div>
          <p className="text-xs text-muted mb-3">
            Observed attributes that reduced the estimated risk indicator or demonstrated compliance.
          </p>

          {protectiveFactors.length === 0 ? (
            <div className="p-3 text-center text-xs text-muted">No mitigating factors identified.</div>
          ) : (
            <div className="flex flex-col gap-2">
              {protectiveFactors.map((f, idx) => (
                <div key={idx} className="p-2 border rounded" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span>{f.feature}</span>
                    <span className="text-success">Mitigation: {f.shap_value?.toFixed(3)}</span>
                  </div>
                  <div className="text-xs text-muted">{f.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Multi-Domain Auditable Evidence Matrix */}
      <div className="card mb-4">
        <div className="card-header">
          <h3>📑 Multi-Domain Auditable Evidence</h3>
          <p className="text-xs text-muted">Extracted across statutory returns, transactional reconciliations, and network logs</p>
        </div>

        <div className="grid grid-3 gap-3 mt-2">
          {/* Reconciliation Evidence */}
          <div className="p-3 border rounded" style={{ background: 'rgba(255,255,255,0.01)' }}>
            <h4 className="text-sm flex items-center gap-1 mb-2 text-primary">
              <Layers size={14} /> Reconciliation Evidence
            </h4>
            <div className="flex flex-col gap-1 text-xs">
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Mismatch Rate:</span>
                <strong>{evidence.reconciliation?.mismatch_rate ? `${(evidence.reconciliation.mismatch_rate * 100).toFixed(1)}%` : '0.0%'}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Mismatched Invoices:</span>
                <strong>{evidence.reconciliation?.mismatch_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Duplicate Invoices:</span>
                <strong>{evidence.reconciliation?.duplicate_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted">Missing e-Invoices:</span>
                <strong>{evidence.reconciliation?.missing_einvoice_count || 0}</strong>
              </div>
            </div>
          </div>

          {/* Statutory Compliance Evidence */}
          <div className="p-3 border rounded" style={{ background: 'rgba(255,255,255,0.01)' }}>
            <h4 className="text-sm flex items-center gap-1 mb-2 text-primary">
              <CheckCircle2 size={14} /> Statutory Compliance
            </h4>
            <div className="flex flex-col gap-1 text-xs">
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Average Filing Delay:</span>
                <strong>{evidence.compliance?.average_filing_delay ? `${evidence.compliance.average_filing_delay} days` : 'On time'}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Late Filings Count:</span>
                <strong>{evidence.compliance?.late_filing_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Missing GSTR-1:</span>
                <strong>{evidence.compliance?.missing_gstr1_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted">Missing GSTR-3B:</span>
                <strong>{evidence.compliance?.missing_gstr3b_count || 0}</strong>
              </div>
            </div>
          </div>

          {/* Network Graph Context */}
          <div className="p-3 border rounded" style={{ background: 'rgba(255,255,255,0.01)' }}>
            <h4 className="text-sm flex items-center gap-1 mb-2 text-primary">
              <Network size={14} /> Knowledge Graph Context
            </h4>
            <div className="flex flex-col gap-1 text-xs">
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Suppliers (Inward):</span>
                <strong>{evidence.graph?.supplier_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Customers (Outward):</span>
                <strong>{evidence.graph?.customer_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1 border-bottom">
                <span className="text-muted">Reciprocal Counterparties:</span>
                <strong>{evidence.graph?.reciprocal_count || 0}</strong>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted">Supplier Concentration:</span>
                <strong>{evidence.graph?.largest_supplier_share_pct ? `${evidence.graph.largest_supplier_share_pct}%` : '0%'}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Risk Evolution & Transition Audit */}
      <div className="card mb-4">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3>📅 Historical Risk Evolution (Chronological Periods)</h3>
            <p className="text-xs text-muted">Trend: <strong>{historyData?.trend?.toUpperCase() || 'STABLE'}</strong> across {historyData?.history?.length || 0} recorded periods</p>
          </div>
          <span className="badge info">Causality Protected (t ≤ T_k)</span>
        </div>

        <div style={{ height: '220px' }} className="mb-3">
          {historyChartData && (
            <Line
              data={historyChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: { min: 0, max: 100 },
                },
              }}
            />
          )}
        </div>

        {/* Transition Table */}
        {historyData?.transitions && historyData.transitions.length > 0 && (
          <div className="mt-3 pt-3 border-top">
            <h4 className="text-xs font-semibold uppercase text-muted mb-2">Period-to-Period Score Transitions</h4>
            <div className="flex flex-wrap gap-2">
              {historyData.transitions.slice(-6).map((t, idx) => (
                <div key={idx} className="p-2 border rounded text-xs" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <div className="font-semibold text-primary">{t.period_transition}</div>
                  <div className="text-muted">{t.class_transition}</div>
                  <div className={t.score_delta > 0 ? 'text-danger' : t.score_delta < 0 ? 'text-success' : 'text-muted'}>
                    Δ {t.score_delta > 0 ? `+${t.score_delta}` : t.score_delta} pts
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
