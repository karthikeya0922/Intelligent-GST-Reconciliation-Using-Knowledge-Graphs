import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  DollarSign,
  TrendingUp,
  AlertTriangle,
  FileText,
  ArrowUpRight,
  ShieldCheck,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { getRiskSummary, getVendors } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

export default function ITCExposureAnalytics() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [topVendors, setTopVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, topRes] = await Promise.all([
        getRiskSummary(),
        getVendors({ sort: 'itc_exposure', order: 'desc', page: 1, page_size: 15 }),
      ]);
      setSummary(sumRes);
      setTopVendors(topRes?.items || []);
    } catch (err) {
      console.error('Failed to load ITC analytics:', err);
      setError(err.message || 'Unable to retrieve ITC exposure data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const exposureTrendData = useMemo(() => {
    if (!summary?.exposure_over_time) return null;
    return {
      labels: summary.exposure_over_time.map((d) => d.period),
      datasets: [
        {
          label: 'Total ITC Financial Exposure',
          data: summary.exposure_over_time.map((d) => d.total_exposure),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          fill: true,
          tension: 0.35,
        },
        {
          label: 'High-Risk ITC Exposure',
          data: summary.exposure_over_time.map((d) => d.high_risk_exposure),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.08)',
          fill: true,
          tension: 0.35,
        },
      ],
    };
  }, [summary]);

  const exposureByRiskClassData = useMemo(() => {
    if (!summary?.exposure_by_risk_class) return null;
    return {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [
        {
          label: 'Exposure (₹)',
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

  if (loading) {
    return (
      <div className="state-container state-loading">
        <div className="spinner" />
        <h3>Loading ITC Exposure Analytics...</h3>
        <p className="text-muted">Aggregating financial discrepancy quantities across benchmark portfolio</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="state-container state-error">
        <AlertCircle size={40} className="error-icon" />
        <h3>Exposure Analytics Error</h3>
        <p className="text-muted">{error}</p>
        <button className="btn-primary mt-2" onClick={loadData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="itc-analytics-page">
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>💰 Input Tax Credit (ITC) Exposure Analytics</h2>
            <p>Financial Exposure Quantification, Risk Class Discrepancy Breakdown & Longitudinal Evolution</p>
          </div>
          <button className="btn-outline flex items-center gap-1" onClick={loadData}>
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </div>

      <ResearchDisclaimer compact />

      {/* Prominent Statutory Notice Required by Spec */}
      <div className="card mb-4" style={{ background: 'rgba(59, 130, 246, 0.05)', borderColor: 'rgba(59, 130, 246, 0.25)' }}>
        <div className="flex items-start gap-3">
          <DollarSign size={20} className="text-info mt-1" />
          <div>
            <h4 className="text-info font-semibold">Financial Exposure Scope & Statutory Clarification</h4>
            <p className="text-xs text-secondary mt-1 leading-relaxed">
              ITC Exposure is a financial quantification associated with reconciliation discrepancies and is not a determination of fraud or legal liability.
              It quantifies the statutory tax credit value potentially subject to inquiry, verification, or provisional hold under GST reconciliation provisions.
            </p>
          </div>
        </div>
      </div>

      {/* 4 Core Financial KPI Cards */}
      <div className="kpi-grid mb-4">
        <div className="kpi-card blue">
          <div className="kpi-label">Total ITC Exposure</div>
          <div className="kpi-value blue">{formatINR(summary?.total_itc_exposure)}</div>
          <div className="kpi-subtext">Cumulative discrepancy value</div>
        </div>

        <div className="kpi-card green">
          <div className="kpi-label">Average Exposure</div>
          <div className="kpi-value green">{formatINR(summary?.average_itc_exposure)}</div>
          <div className="kpi-subtext">Across {summary?.total_vendors} entities</div>
        </div>

        <div className="kpi-card red">
          <div className="kpi-label">High-Risk ITC Exposure</div>
          <div className="kpi-value red">{formatINR(summary?.high_risk_itc_exposure)}</div>
          <div className="kpi-subtext">High Risk Band entities</div>
        </div>

        <div className="kpi-card purple">
          <div className="kpi-label">Active Evaluation Period</div>
          <div className="kpi-value purple">{summary?.period || '2026-02'}</div>
          <div className="kpi-subtext">Latest benchmark observation</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-2 gap-3 mb-4">
        <div className="card">
          <div className="card-header">
            <h3>📊 Financial Exposure by Model Risk Class</h3>
          </div>
          <div style={{ height: '230px' }}>
            {exposureByRiskClassData && (
              <Bar
                data={exposureByRiskClassData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                }}
              />
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>📈 Portfolio Exposure Trend (24 Tax Periods)</h3>
          </div>
          <div style={{ height: '230px' }}>
            {exposureTrendData && (
              <Line
                data={exposureTrendData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                }}
              />
            )}
          </div>
        </div>
      </div>

      {/* Top 15 Vendor Exposure Ranking Table */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div>
            <h3>🏆 Vendor ITC Exposure Ranking (Top 15 Material Entities)</h3>
            <p className="text-xs text-muted">Ranked strictly by monetary ITC exposure magnitude</p>
          </div>
          <button className="btn-outline btn-sm" onClick={() => navigate('/vendors?sort=itc_exposure&order=desc')}>
            View All Vendors in Table
          </button>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Vendor</th>
                <th>ITC Exposure</th>
                <th>Risk Band</th>
                <th>0–100 Score</th>
                <th>Operational Priority</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {topVendors.map((v, idx) => (
                <tr key={v.vendor_id} className="hover-row">
                  <td className="font-mono text-muted">#{idx + 1}</td>
                  <td>
                    <div className="font-semibold text-primary">{v.vendor_name}</div>
                    <div className="text-xs text-muted">{v.vendor_id} • {v.gstin}</div>
                  </td>
                  <td className="font-semibold text-danger">{formatINR(v.itc_exposure)}</td>
                  <td>
                    <span className={`badge-${v.risk_band?.toLowerCase() || 'low'}`}>{v.risk_band}</span>
                  </td>
                  <td className="font-mono">{v.risk_score?.toFixed(1)}</td>
                  <td>
                    <span className={`badge-${v.priority?.toLowerCase() || 'low'}`}>{v.priority}</span>
                  </td>
                  <td className="text-right">
                    <button
                      className="btn-sm btn-outline flex items-center gap-1 ml-auto"
                      onClick={() => navigate(`/vendors/${v.vendor_id}`)}
                    >
                      Inspect <ArrowUpRight size={12} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
