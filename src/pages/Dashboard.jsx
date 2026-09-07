import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  TrendingUp,
  ShieldAlert,
  Users,
  AlertCircle,
  FileSearch,
  Network,
  RefreshCw,
  ArrowUpRight,
  ShieldCheck,
  DollarSign
} from 'lucide-react';
import { getRiskSummary } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toFixed(0)}`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRiskSummary();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load risk summary:', err);
      setError(err.message || 'Unable to load risk intelligence metrics from backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  // Risk Distribution Chart (Doughnut)
  const riskDoughnutData = useMemo(() => {
    if (!summary?.risk_distribution) return null;
    return {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [
        {
          data: [
            summary.risk_distribution.LOW || 0,
            summary.risk_distribution.MEDIUM || 0,
            summary.risk_distribution.HIGH || 0,
          ],
          backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
          borderColor: '#1a2035',
          borderWidth: 3,
          hoverOffset: 6,
        },
      ],
    };
  }, [summary]);

  // ITC Exposure Breakdown by Risk Class (Bar)
  const exposureBarData = useMemo(() => {
    if (!summary?.exposure_by_risk_class) return null;
    return {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [
        {
          label: 'ITC Exposure (₹)',
          data: [
            summary.exposure_by_risk_class.LOW || 0,
            summary.exposure_by_risk_class.MEDIUM || 0,
            summary.exposure_by_risk_class.HIGH || 0,
          ],
          backgroundColor: ['rgba(34, 197, 94, 0.7)', 'rgba(245, 158, 11, 0.7)', 'rgba(239, 68, 68, 0.7)'],
          borderColor: ['#22c55e', '#f59e0b', '#ef4444'],
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    };
  }, [summary]);

  // Exposure Over Time Line Chart
  const exposureTrendData = useMemo(() => {
    if (!summary?.exposure_over_time || summary.exposure_over_time.length === 0) return null;
    const labels = summary.exposure_over_time.map(d => d.period);
    const totals = summary.exposure_over_time.map(d => d.total_exposure);
    const highRisks = summary.exposure_over_time.map(d => d.high_risk_exposure);

    return {
      labels,
      datasets: [
        {
          label: 'Total ITC Exposure',
          data: totals,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        },
        {
          label: 'High-Risk ITC Exposure',
          data: highRisks,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.08)',
          fill: true,
          tension: 0.35,
          pointRadius: 2,
        },
      ],
    };
  }, [summary]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, boxWidth: 12 } },
      tooltip: {
        backgroundColor: '#1a2035',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        titleColor: '#f1f5f9',
        bodyColor: '#94a3b8',
        padding: 10,
        cornerRadius: 6,
      },
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } },
      y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } },
    },
  };

  if (loading) {
    return (
      <div className="state-container state-loading">
        <div className="spinner" />
        <h3>Loading Risk Intelligence Data...</h3>
        <p className="text-muted">Calculating dynamic metrics over 46,345 benchmark observations</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container state-error">
        <AlertCircle size={48} className="error-icon" />
        <h3>Unable to Load Dashboard Data</h3>
        <p className="text-muted">{error}</p>
        <button className="btn-primary mt-2 flex items-center gap-1" onClick={fetchSummary}>
          <RefreshCw size={14} /> Retry Connection
        </button>
      </div>
    );
  }

  const highPriorityCount =
    (summary?.operational_priority_distribution?.CRITICAL || 0) +
    (summary?.operational_priority_distribution?.HIGH || 0);

  return (
    <div className="dashboard-container">
      {/* Page Header */}
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>📊 GST Risk Intelligence Dashboard</h2>
            <p>Predictive ML Decision Support, Financial ITC Exposure & Knowledge Graph Network Context</p>
          </div>
          <div className="flex gap-1 items-center">
            <span className="badge info">Evaluation Period: {summary?.period || '2026-02'}</span>
            <button className="btn-outline flex items-center gap-1" onClick={fetchSummary} title="Refresh dataset metrics">
              <RefreshCw size={13} /> Refresh
            </button>
          </div>
        </div>
      </div>

      <ResearchDisclaimer />

      {/* 6 Core KPI Cards (Backend Sources of Truth) */}
      <div className="kpi-grid mb-4">
        <div className="kpi-card blue">
          <div className="kpi-label flex items-center justify-between">
            <span>Total Vendors</span>
            <Users size={16} className="text-muted" />
          </div>
          <div className="kpi-value blue">{summary?.total_vendors?.toLocaleString() || 0}</div>
          <div className="kpi-subtext">Active simulated benchmark entities</div>
        </div>

        <div className="kpi-card red">
          <div className="kpi-label flex items-center justify-between">
            <span>Total ITC Exposure</span>
            <DollarSign size={16} className="text-muted" />
          </div>
          <div className="kpi-value red">{formatINR(summary?.total_itc_exposure)}</div>
          <div className="kpi-subtext">Avg: {formatINR(summary?.average_itc_exposure)} / vendor</div>
        </div>

        <div className="kpi-card orange">
          <div className="kpi-label flex items-center justify-between">
            <span>High Risk Vendors</span>
            <ShieldAlert size={16} className="text-muted" />
          </div>
          <div className="kpi-value orange">{summary?.risk_distribution?.HIGH?.toLocaleString() || 0}</div>
          <div className="kpi-subtext">{summary?.risk_percentages?.HIGH || 0}% of portfolio</div>
        </div>

        <div className="kpi-card yellow">
          <div className="kpi-label flex items-center justify-between">
            <span>Medium Risk Vendors</span>
            <AlertCircle size={16} className="text-muted" />
          </div>
          <div className="kpi-value yellow">{summary?.risk_distribution?.MEDIUM?.toLocaleString() || 0}</div>
          <div className="kpi-subtext">{summary?.risk_percentages?.MEDIUM || 0}% of portfolio</div>
        </div>

        <div className="kpi-card green">
          <div className="kpi-label flex items-center justify-between">
            <span>Low Risk Vendors</span>
            <ShieldCheck size={16} className="text-muted" />
          </div>
          <div className="kpi-value green">{summary?.risk_distribution?.LOW?.toLocaleString() || 0}</div>
          <div className="kpi-subtext">{summary?.risk_percentages?.LOW || 0}% of portfolio</div>
        </div>

        <div className="kpi-card purple">
          <div className="kpi-label flex items-center justify-between">
            <span>High/Critical Priority</span>
            <TrendingUp size={16} className="text-muted" />
          </div>
          <div className="kpi-value purple">{highPriorityCount.toLocaleString()}</div>
          <div className="kpi-subtext">Requires immediate desk/field review</div>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-2 mb-4 gap-3">
        {/* Risk Distribution Chart */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3>🎯 ML Risk Distribution</h3>
            <Link to="/vendors" className="text-accent text-xs flex items-center gap-1">
              View Vendors <ArrowUpRight size={12} />
            </Link>
          </div>
          <div style={{ height: '230px' }} className="flex items-center justify-center">
            {riskDoughnutData && <Doughnut data={riskDoughnutData} options={{ maintainAspectRatio: false }} />}
          </div>
          <div className="flex justify-around text-xs text-muted mt-2 pt-2 border-top">
            <span>🟢 Low: {summary?.risk_distribution?.LOW} ({summary?.risk_percentages?.LOW}%)</span>
            <span>🟡 Medium: {summary?.risk_distribution?.MEDIUM} ({summary?.risk_percentages?.MEDIUM}%)</span>
            <span>🔴 High: {summary?.risk_distribution?.HIGH} ({summary?.risk_percentages?.HIGH}%)</span>
          </div>
        </div>

        {/* ITC Exposure by Risk Band */}
        <div className="card">
          <div className="card-header flex items-center justify-between">
            <h3>💰 Financial ITC Exposure by Risk Class</h3>
            <Link to="/itc-exposure" className="text-accent text-xs flex items-center gap-1">
              ITC Analytics <ArrowUpRight size={12} />
            </Link>
          </div>
          <div style={{ height: '230px' }}>
            {exposureBarData && <Bar data={exposureBarData} options={chartOptions} />}
          </div>
          <div className="text-xs text-muted mt-2 pt-2 border-top flex justify-between">
            <span>High Risk Exposure: <strong>{formatINR(summary?.high_risk_itc_exposure)}</strong></span>
            <span>Portfolio Exposure: <strong>{formatINR(summary?.total_itc_exposure)}</strong></span>
          </div>
        </div>
      </div>

      {/* 24-Month Exposure Trend Chart */}
      <div className="card mb-4">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3>📈 ITC Financial Exposure Trend (24 Simulated Tax Months)</h3>
            <p className="text-xs text-muted">Chronological exposure evolution across all benchmark periods</p>
          </div>
          <span className="badge info">t ≤ {summary?.period}</span>
        </div>
        <div style={{ height: '260px' }}>
          {exposureTrendData && <Line data={exposureTrendData} options={chartOptions} />}
        </div>
      </div>

      {/* Risk x Exposure Operational Prioritization Matrix */}
      <div className="matrix-card mb-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3>⚖️ Risk × Exposure Operational Prioritization Matrix</h3>
            <p className="text-xs text-muted">
              Decouples ML Model Risk Class from Financial ITC Exposure. Click any cell to inspect filtered vendors.
            </p>
          </div>
          <span className="text-xs text-muted">Threshold: ₹100,000 Materiality</span>
        </div>

        <div className="matrix-grid">
          {/* Header Row */}
          <div className="matrix-header-cell">Risk Band \ Exposure</div>
          <div className="matrix-header-cell">Low Exposure (&lt; ₹1.0L)</div>
          <div className="matrix-header-cell">High Exposure (≥ ₹1.0L)</div>

          {/* HIGH RISK ROW */}
          <div className="matrix-row-label">
            <span className="badge-high mb-1">HIGH RISK</span>
            <span className="text-xs text-muted">Score &gt; 66</span>
          </div>
          {summary?.risk_exposure_matrix
            ?.filter(c => c.risk_band === 'HIGH')
            ?.map((cell, idx) => (
              <div
                key={idx}
                className="matrix-interactive-cell"
                onClick={() => navigate(`/vendors?risk_class=HIGH&priority=${cell.priority}`)}
                title="Click to view vendors in this category"
              >
                <div className="flex items-center justify-between">
                  <div className="cell-vendors">{cell.vendor_count} Vendors</div>
                  <span className={`badge-${cell.priority.toLowerCase()}`}>{cell.priority}</span>
                </div>
                <div className="cell-exposure">{formatINR(cell.total_exposure)} exposure</div>
                <div className="cell-action">{cell.action}</div>
              </div>
            ))}

          {/* MEDIUM RISK ROW */}
          <div className="matrix-row-label">
            <span className="badge-medium mb-1">MEDIUM RISK</span>
            <span className="text-xs text-muted">Score 33–66</span>
          </div>
          {summary?.risk_exposure_matrix
            ?.filter(c => c.risk_band === 'MEDIUM')
            ?.map((cell, idx) => (
              <div
                key={idx}
                className="matrix-interactive-cell"
                onClick={() => navigate(`/vendors?risk_class=MEDIUM&priority=${cell.priority}`)}
                title="Click to view vendors in this category"
              >
                <div className="flex items-center justify-between">
                  <div className="cell-vendors">{cell.vendor_count} Vendors</div>
                  <span className={`badge-${cell.priority.toLowerCase()}`}>{cell.priority}</span>
                </div>
                <div className="cell-exposure">{formatINR(cell.total_exposure)} exposure</div>
                <div className="cell-action">{cell.action}</div>
              </div>
            ))}

          {/* LOW RISK ROW */}
          <div className="matrix-row-label">
            <span className="badge-low mb-1">LOW RISK</span>
            <span className="text-xs text-muted">Score 0–33</span>
          </div>
          {summary?.risk_exposure_matrix
            ?.filter(c => c.risk_band === 'LOW')
            ?.map((cell, idx) => (
              <div
                key={idx}
                className="matrix-interactive-cell"
                onClick={() => navigate(`/vendors?risk_class=LOW&priority=${cell.priority}`)}
                title="Click to view vendors in this category"
              >
                <div className="flex items-center justify-between">
                  <div className="cell-vendors">{cell.vendor_count} Vendors</div>
                  <span className={`badge-${cell.priority.toLowerCase()}`}>{cell.priority}</span>
                </div>
                <div className="cell-exposure">{formatINR(cell.total_exposure)} exposure</div>
                <div className="cell-action">{cell.action}</div>
              </div>
            ))}
        </div>
      </div>

      {/* Fast Navigation Quick Links */}
      <div className="grid grid-3 gap-3">
        <div className="card clickable-card" onClick={() => navigate('/vendors')}>
          <div className="flex items-center gap-2 mb-1">
            <Users size={18} className="text-accent" />
            <h4>Vendor Risk Directory</h4>
          </div>
          <p className="text-xs text-muted">
            Search, sort, and filter all 2,015 vendors with 0–100 scores and financial exposure.
          </p>
        </div>

        <div className="card clickable-card" onClick={() => navigate('/investigation')}>
          <div className="flex items-center gap-2 mb-1">
            <FileSearch size={18} className="text-accent" />
            <h4>Investigation Workspace</h4>
          </div>
          <p className="text-xs text-muted">
            7-step unified analyst review workstation combining SHAP factors, evidence, and graph signals.
          </p>
        </div>

        <div className="card clickable-card" onClick={() => navigate('/graph')}>
          <div className="flex items-center gap-2 mb-1">
            <Network size={18} className="text-accent" />
            <h4>Knowledge Graph Explorer</h4>
          </div>
          <p className="text-xs text-muted">
            Time-safe commercial topology exploration with depth 1/2 counterparty concentration.
          </p>
        </div>
      </div>
    </div>
  );
}
