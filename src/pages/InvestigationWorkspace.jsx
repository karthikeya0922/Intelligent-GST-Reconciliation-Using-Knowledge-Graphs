import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileSearch,
  Search,
  ShieldAlert,
  DollarSign,
  TrendingUp,
  Layers,
  CheckCircle2,
  Network,
  Download,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  ChevronRight,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { getVendor, getVendorGraph, getVendors } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

const STEPS = [
  { id: 1, title: 'Vendor Identity' },
  { id: 2, title: 'ML Risk Score' },
  { id: 3, title: 'ITC Exposure' },
  { id: 4, title: 'SHAP Factors' },
  { id: 5, title: 'Reconciliation' },
  { id: 6, title: 'Compliance' },
  { id: 7, title: 'Knowledge Graph' },
  { id: 8, title: 'Review Priority' },
];

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

function getEvidenceValue(evidenceSource, summarySource, featureName, defaultValue = 0) {
  if (summarySource && summarySource[featureName] !== undefined) {
    return summarySource[featureName];
  }
  if (Array.isArray(evidenceSource)) {
    const item = evidenceSource.find(e => e.feature === featureName);
    return item && item.value !== undefined ? item.value : defaultValue;
  }
  if (evidenceSource && typeof evidenceSource === 'object' && evidenceSource[featureName] !== undefined) {
    return evidenceSource[featureName];
  }
  return defaultValue;
}

export default function InvestigationWorkspace() {
  const { vendor_id } = useParams();
  const navigate = useNavigate();

  const [currentVendorId, setCurrentVendorId] = useState(vendor_id || 'V0001');
  const [searchInput, setSearchInput] = useState(vendor_id || 'V0001');
  const [currentStep, setCurrentStep] = useState(1);

  const [assessment, setAssessment] = useState(null);
  const [graphContext, setGraphContext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async (vid) => {
    setLoading(true);
    setError(null);
    try {
      const [vData, gData] = await Promise.all([
        getVendor(vid),
        getVendorGraph(vid, '2026-02', 1).catch(() => null),
      ]);
      setAssessment(vData);
      setGraphContext(gData);
      setCurrentVendorId(vid);
    } catch (err) {
      console.error('Failed to load investigation data:', err);
      setError(err.message || `Unable to load assessment records for '${vid}'.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (vendor_id) {
      setCurrentVendorId(vendor_id);
      setSearchInput(vendor_id);
      loadData(vendor_id);
    } else {
      loadData(currentVendorId);
    }
  }, [vendor_id]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      navigate(`/investigation/${searchInput.trim().toUpperCase()}`);
    }
  };

  const handleExportAudit = () => {
    if (!assessment) return;
    const auditRecord = {
      audit_export_timestamp: new Date().toISOString(),
      vendor_id: currentVendorId,
      prediction_period: assessment.prediction_period,
      risk_evaluation: assessment.risk,
      financial_itc_exposure: assessment.itc,
      recommendations: assessment.recommendations,
      tree_shap_explanation: assessment.explanation,
      auditable_evidence: assessment.evidence,
      network_graph_signals: graphContext?.metadata || {},
      disclaimer: 'Demonstrated on controlled hybrid research benchmark. Not a determination of fraud or statutory liability.'
    };

    const blob = new Blob([JSON.stringify(auditRecord, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `GST_Audit_Report_${currentVendorId}_${assessment.prediction_period}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const risk = assessment?.risk || {};
  const itc = assessment?.itc || {};
  const evidence = assessment?.evidence || {};
  const evidenceSummary = assessment?.evidence_summary || {};
  const rawShap = assessment?.explanation?.top_contributing_factors;
  const shapFactors = (rawShap && rawShap.length > 0)
    ? rawShap
    : (assessment?.evidence?.model || assessment?.top_factors || []).map(m => {
        const match = m.description?.match(/impact\s+([+-]?\d+\.?\d*)/);
        const val = match ? parseFloat(match[1]) : (typeof m.shap_value === 'number' ? m.shap_value : (typeof m.value === 'number' ? m.value : 0.05));
        return {
          feature: m.feature,
          description: m.description,
          shap_value: val,
          impact: m.severity?.toLowerCase() || m.impact || 'medium'
        };
      });
  const protectiveFactors = assessment?.explanation?.protective_factors || [];

  return (
    <div className="investigation-workspace-page">
      {/* Page Header */}
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>🔬 GST Investigation Workspace</h2>
            <p>Unified 8-Step Auditor Review Flow: Risk Evaluation, Financial Exposure, SHAP & Knowledge Graph</p>
          </div>
          <div className="flex gap-2">
            <button
              className="btn-outline flex items-center gap-1"
              onClick={handleExportAudit}
              disabled={!assessment}
              title="Download audit-ready JSON report"
            >
              <Download size={13} /> Export Audit File
            </button>
          </div>
        </div>
      </div>

      <ResearchDisclaimer compact />

      {/* Vendor Selector Form */}
      <div className="filter-bar mb-3">
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1">
          <Search size={16} className="text-muted" />
          <input
            type="text"
            className="filter-input"
            placeholder="Search Vendor (e.g. V0001, V0005, V0010)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit" className="btn-primary btn-sm">Load Case</button>
        </form>

        <div className="flex items-center gap-1 text-xs text-muted">
          <span>Quick Benchmark Cases:</span>
          {['V0001', 'V0002', 'V0005', 'V0010', 'V0018'].map((v) => (
            <button
              key={v}
              className={`badge-tag ${currentVendorId === v ? 'active-tag' : ''}`}
              onClick={() => navigate(`/investigation/${v}`)}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="state-container state-loading">
          <div className="spinner" />
          <h3>Retrieving Investigation Dossier for {currentVendorId}...</h3>
          <p className="text-muted">Extracting multi-domain evidence, Tree SHAP explanations, and network ties</p>
        </div>
      ) : error ? (
        <div className="state-container state-error">
          <AlertCircle size={40} className="error-icon" />
          <h3>Dossier Loading Error</h3>
          <p className="text-muted">{error}</p>
        </div>
      ) : (
        <>
          {/* 8-Step Visual Stepper */}
          <div className="workflow-stepper">
            {STEPS.map((s) => (
              <div
                key={s.id}
                className={`step-item ${currentStep === s.id ? 'active' : currentStep > s.id ? 'completed' : ''}`}
                onClick={() => setCurrentStep(s.id)}
              >
                <div className="step-number">{s.id}</div>
                <span>{s.title}</span>
              </div>
            ))}
          </div>

          {/* Stepper Content Panels */}
          <div className="card mb-4" style={{ minHeight: '380px' }}>
            {/* STEP 1: Vendor Identity */}
            {currentStep === 1 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 1 — Entity Identity & Filing Demographics</h3>
                  <span className="badge info">{currentVendorId}</span>
                </div>
                <div className="grid grid-2 gap-3 text-sm">
                  <div className="p-3 border rounded">
                    <h4 className="text-muted text-xs mb-2 uppercase">Taxpayer Details</h4>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Vendor ID:</span>
                      <strong>{assessment.vendor_id}</strong>
                    </div>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Observation Period:</span>
                      <strong>{assessment.prediction_period}</strong>
                    </div>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Data Source:</span>
                      <span>Hybrid Synthetic Benchmark</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-muted">State Jurisdiction:</span>
                      <span>Registered Active Entity</span>
                    </div>
                  </div>

                  <div className="p-3 border rounded">
                    <h4 className="text-muted text-xs mb-2 uppercase">Filing Profile</h4>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Total Monthly Invoices:</span>
                      <strong>{itc.total_invoices || evidence.reconciliation?.total_invoices || 'N/A'}</strong>
                    </div>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Invoice Turnover:</span>
                      <strong>{formatINR(itc.total_invoice_value)}</strong>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-muted">Tax Billed:</span>
                      <strong>{formatINR(itc.total_tax)}</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: Review Risk */}
            {currentStep === 2 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 2 — Tabular XGBoost ML Risk Indicator</h3>
                  <span className={`badge-${risk.model_class?.toLowerCase() || 'low'}`}>
                    Class: {risk.model_class}
                  </span>
                </div>
                <div className="grid grid-2 gap-4">
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Normalized 0–100 ML Score</h4>
                    <div className="kpi-value orange mb-2">{risk.score?.toFixed(1)} / 100</div>
                    <p className="text-xs text-muted leading-relaxed">
                      Derived via class probabilities: <code>Score = 100 × [0.5 × P(MED) + 1.0 × P(HIGH)]</code>.
                      Decoupled strictly from statutory fraud determinations.
                    </p>
                  </div>

                  <div className="p-3 border rounded">
                    <h4 className="text-xs uppercase text-muted mb-2">Model Class Probabilities</h4>
                    <div className="flex justify-between py-1 border-bottom text-xs">
                      <span>P(LOW Risk):</span>
                      <strong>{(risk.probabilities?.LOW * 100).toFixed(2)}%</strong>
                    </div>
                    <div className="flex justify-between py-1 border-bottom text-xs">
                      <span>P(MEDIUM Risk):</span>
                      <strong>{(risk.probabilities?.MEDIUM * 100).toFixed(2)}%</strong>
                    </div>
                    <div className="flex justify-between py-1 text-xs">
                      <span>P(HIGH Risk):</span>
                      <strong>{(risk.probabilities?.HIGH * 100).toFixed(2)}%</strong>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: Review ITC Exposure */}
            {currentStep === 3 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 3 — Financial ITC Exposure Quantification</h3>
                  <span className="badge danger">Exposure: {formatINR(itc.exposure)}</span>
                </div>
                <p className="text-xs text-muted mb-3">
                  Financial quantification of potential Input Tax Credit exposure arising from reconciliation mismatches,
                  omissions, or timing discrepancies.
                </p>
                <div className="grid grid-3 gap-3">
                  <div className="kpi-card">
                    <div className="kpi-label">Total Tax Amount</div>
                    <div className="kpi-value">{formatINR(itc.total_tax)}</div>
                  </div>
                  <div className="kpi-card red">
                    <div className="kpi-label">ITC Exposure Amount</div>
                    <div className="kpi-value red">{formatINR(itc.exposure)}</div>
                  </div>
                  <div className="kpi-card">
                    <div className="kpi-label">Exposure Ratio</div>
                    <div className="kpi-value">{((itc.exposure_ratio || 0) * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 4: Review SHAP Factors */}
            {currentStep === 4 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 4 — Tree SHAP Factor Attributions</h3>
                  <span className="text-xs text-muted">Feature Importance</span>
                </div>
                <p className="text-xs text-muted mb-3">
                  Exact additive Shapley contributions showing which specific compliance attributes drove the model score.
                </p>

                {shapFactors.length === 0 && protectiveFactors.length === 0 ? (
                  <div className="p-4 text-center border rounded" style={{ background: 'rgba(255,255,255,0.02)' }}>
                    <p className="text-sm font-medium text-muted">No material upward risk factors detected.</p>
                    <p className="text-xs text-muted mt-1">This vendor exhibits compliant return filing and standard commercial patterns.</p>
                  </div>
                ) : (
                  <>
                    <div className="flex flex-col gap-2">
                      {shapFactors.map((f, idx) => (
                        <div key={idx} className="p-3 border rounded flex justify-between items-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                          <div>
                            <div className="font-semibold text-sm">{f.feature?.replace(/_/g, ' ')}</div>
                            <div className="text-xs text-muted">{f.description}</div>
                          </div>
                          <div className="text-right">
                            <span className={f.shap_value >= 0 ? "badge-high" : "badge-low"}>
                              {typeof f.shap_value === 'number' ? (f.shap_value >= 0 ? `+${f.shap_value.toFixed(3)}` : f.shap_value.toFixed(3)) : '+0.050'}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {protectiveFactors.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-xs uppercase text-muted mb-2 font-semibold">🛡️ Mitigating / Protective Factors</h4>
                        <div className="flex flex-col gap-2">
                          {protectiveFactors.map((f, idx) => (
                            <div key={idx} className="p-3 border rounded flex justify-between items-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                              <div>
                                <div className="font-semibold text-sm">{f.feature?.replace(/_/g, ' ')}</div>
                                <div className="text-xs text-muted">{f.description}</div>
                              </div>
                              <div className="text-right">
                                <span className="badge-low">
                                  {typeof f.shap_value === 'number' ? f.shap_value.toFixed(3) : '-0.050'}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* STEP 5: Review Reconciliation */}
            {currentStep === 5 && (() => {
              const mismatchRate = getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'mismatch_rate', 0);
              const mismatchCount = getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'mismatch_count', 0);
              const duplicateCount = getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'duplicate_invoice_count', getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'duplicate_count', 0));
              const missingEinvoice = getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'missing_einvoice_count', 0);
              const missingEway = getEvidenceValue(evidence.reconciliation, evidenceSummary.reconciliation, 'missing_eway_bill_count', 0);
              const reconItems = Array.isArray(evidence.reconciliation) ? evidence.reconciliation : [];

              return (
                <div>
                  <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                    <h3>Step 5 — Invoice Reconciliation Signals</h3>
                    <span className="badge warning">Reconciliation Audit</span>
                  </div>
                  <div className="grid grid-2 gap-3 text-xs mb-3">
                    <div className="p-3 border rounded">
                      <div className="flex justify-between py-1 border-bottom">
                        <span className="text-muted">Taxable Value Mismatch Rate:</span>
                        <strong className={mismatchRate > 0.05 ? "text-danger" : ""}>{(mismatchRate * 100).toFixed(1)}%</strong>
                      </div>
                      <div className="flex justify-between py-1 border-bottom">
                        <span className="text-muted">Total Discrepant Invoices:</span>
                        <strong className={mismatchCount > 0 ? "text-danger" : ""}>{mismatchCount}</strong>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-muted">Duplicate Invoices:</span>
                        <strong>{duplicateCount}</strong>
                      </div>
                    </div>

                    <div className="p-3 border rounded">
                      <div className="flex justify-between py-1 border-bottom">
                        <span className="text-muted">Missing e-Invoice IRN:</span>
                        <strong className={missingEinvoice > 0 ? "text-warning" : ""}>{missingEinvoice}</strong>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-muted">Missing e-Way Bill Coverage:</span>
                        <strong className={missingEway > 0 ? "text-warning" : ""}>{missingEway}</strong>
                      </div>
                    </div>
                  </div>

                  {reconItems.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-xs uppercase text-muted mb-2 font-semibold">📑 Auditable Reconciliation Discrepancies</h4>
                      <div className="flex flex-col gap-2">
                        {reconItems.map((item, idx) => (
                          <div key={idx} className="p-2 border rounded text-xs flex justify-between items-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <span>{item.description}</span>
                            <span className={item.severity === 'HIGH' ? 'badge-high' : 'badge-warning'}>{item.severity}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* STEP 6: Review Compliance */}
            {currentStep === 6 && (() => {
              const avgDelay = getEvidenceValue(evidence.compliance, evidenceSummary.compliance, 'average_filing_delay', 0);
              const lateCount = getEvidenceValue(evidence.compliance, evidenceSummary.compliance, 'late_filing_count', 0);
              const missingGstr1 = getEvidenceValue(evidence.compliance, evidenceSummary.compliance, 'missing_gstr1_count', 0);
              const missingGstr3b = getEvidenceValue(evidence.compliance, evidenceSummary.compliance, 'missing_gstr3b_count', 0);
              const compItems = Array.isArray(evidence.compliance) ? evidence.compliance : [];

              return (
                <div>
                  <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                    <h3>Step 6 — Statutory Compliance & Return Filings</h3>
                    <span className="badge info">Statutory History</span>
                  </div>
                  <div className="grid grid-2 gap-3 text-xs mb-3">
                    <div className="p-3 border rounded">
                      <div className="flex justify-between py-1 border-bottom">
                        <span className="text-muted">Average GSTR-1 Filing Delay:</span>
                        <strong className={avgDelay > 0 ? "text-warning" : ""}>{avgDelay > 0 ? `${avgDelay} days` : '0 days (on time)'}</strong>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-muted">Late Filing Frequency:</span>
                        <strong className={lateCount > 0 ? "text-warning" : ""}>{lateCount} period(s)</strong>
                      </div>
                    </div>

                    <div className="p-3 border rounded">
                      <div className="flex justify-between py-1 border-bottom">
                        <span className="text-muted">Omitted GSTR-1 Returns:</span>
                        <strong className={missingGstr1 > 0 ? "text-danger" : ""}>{missingGstr1}</strong>
                      </div>
                      <div className="flex justify-between py-1">
                        <span className="text-muted">Defaulted GSTR-3B Tax Remittances:</span>
                        <strong className={missingGstr3b > 0 ? "text-danger" : ""}>{missingGstr3b}</strong>
                      </div>
                    </div>
                  </div>

                  {compItems.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-xs uppercase text-muted mb-2 font-semibold">📑 Statutory Return Audit Findings</h4>
                      <div className="flex flex-col gap-2">
                        {compItems.map((item, idx) => (
                          <div key={idx} className="p-2 border rounded text-xs flex justify-between items-center" style={{ background: 'rgba(255,255,255,0.02)' }}>
                            <span>{item.description}</span>
                            <span className={item.severity === 'HIGH' ? 'badge-high' : 'badge-warning'}>{item.severity}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* STEP 7: Inspect Knowledge Graph */}
            {currentStep === 7 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 7 — Knowledge Graph Topology & Counterparty Signals</h3>
                  <button
                    className="btn-outline btn-sm flex items-center gap-1"
                    onClick={() => navigate(`/graph?vendor=${currentVendorId}`)}
                  >
                    Open Full Graph <ExternalLink size={12} />
                  </button>
                </div>
                <div className="grid grid-2 gap-3 text-xs">
                  <div className="p-3 border rounded">
                    <h4 className="text-muted uppercase text-xs mb-2">Trading Network Summary</h4>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Active Direct Counterparties:</span>
                      <strong>{(graphContext?.nodes?.length ? graphContext.nodes.length - 1 : 0)} connected nodes</strong>
                    </div>
                    <div className="flex justify-between py-1 border-bottom">
                      <span className="text-muted">Supplier Concentration:</span>
                      <strong>{graphContext?.metadata?.supplier_concentration_pct || 0}%</strong>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-muted">Customer Concentration:</span>
                      <strong>{graphContext?.metadata?.customer_concentration_pct || 0}%</strong>
                    </div>
                  </div>

                  <div className="p-3 border rounded">
                    <h4 className="text-muted uppercase text-xs mb-2">Network Flags</h4>
                    {graphContext?.metadata?.network_flags?.length === 0 ? (
                      <p className="text-muted">No high concentration or cyclical trading flags observed.</p>
                    ) : (
                      graphContext?.metadata?.network_flags?.map((f, i) => (
                        <div key={i} className="mb-1 text-warning">• {f}</div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* STEP 8: Review Operational Priority */}
            {currentStep === 8 && (
              <div>
                <div className="card-header flex items-center justify-between border-bottom pb-2 mb-3">
                  <h3>Step 8 — Operational Review Decision & Action Hold</h3>
                  <span className={`badge-${rec.review_priority?.toLowerCase() || 'low'}`}>
                    Priority: {rec.review_priority}
                  </span>
                </div>
                <div className="p-4 border rounded mb-3" style={{ background: 'rgba(255,255,255,0.02)' }}>
                  <h4 className="text-sm font-bold text-accent mb-2">
                    Recommended Action: {rec.recommended_action}
                  </h4>
                  <p className="text-xs text-muted leading-relaxed mb-3">
                    {rec.review_details}
                  </p>
                  <div className="flex gap-2">
                    <button className="btn-primary btn-sm flex items-center gap-1" onClick={handleExportAudit}>
                      <Download size={12} /> Confirm & Save Audit Dossier
                    </button>
                    <button className="btn-outline btn-sm" onClick={() => navigate('/vendors')}>
                      Complete Case & Next Vendor
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex justify-between items-center">
            <button
              className="btn-outline flex items-center gap-1"
              disabled={currentStep <= 1}
              onClick={() => setCurrentStep((s) => Math.max(1, s - 1))}
            >
              <ArrowLeft size={14} /> Previous Step
            </button>

            <span className="text-xs text-muted">
              Step {currentStep} of {STEPS.length}: <strong>{STEPS[currentStep - 1].title}</strong>
            </span>

            <button
              className="btn-primary flex items-center gap-1"
              disabled={currentStep >= STEPS.length}
              onClick={() => setCurrentStep((s) => Math.min(STEPS.length, s + 1))}
            >
              Next Step <ArrowRight size={14} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
