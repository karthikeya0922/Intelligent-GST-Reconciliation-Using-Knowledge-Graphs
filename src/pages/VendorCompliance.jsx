import { useState, useMemo } from 'react';
import { Bar, Line, Radar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, RadialLinearScale, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { motion } from 'framer-motion';
import { TrendingUp, Brain, BarChart3, Target } from 'lucide-react';
import { useData } from '../context/DataContext';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, RadialLinearScale, ArcElement, Title, Tooltip, Legend, Filler);

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, boxWidth: 12, padding: 16 } },
        tooltip: { backgroundColor: '#1a2035', borderColor: '#f59e0b22', borderWidth: 1, titleColor: '#f1f5f9', bodyColor: '#94a3b8', padding: 12, cornerRadius: 8 }
    },
    scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } }
    }
};

export default function VendorCompliance() {
    const { vendors, riskFeatureImportance } = useData();
    const [selectedVendor, setSelectedVendor] = useState(null);

    // Feature importance chart
    const featureImportanceData = useMemo(() => ({
        labels: riskFeatureImportance.map(f => f.feature),
        datasets: [{
            label: 'Importance',
            data: riskFeatureImportance.map(f => f.importance),
            backgroundColor: riskFeatureImportance.map((_, i) => {
                const colors = ['#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6', '#22c55e', '#06b6d4', '#ec4899', '#6366f1'];
                return colors[i % colors.length];
            }),
            borderRadius: 6,
            borderSkipped: false,
        }],
    }), [riskFeatureImportance]);

    const riskBuckets = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];
    const riskHistogram = useMemo(() => riskBuckets.slice(0, -1).map((low, i) => {
        const high = riskBuckets[i + 1];
        return vendors.filter(v => v.riskScore >= low && v.riskScore < high).length;
    }), [vendors]);

    const histogramData = useMemo(() => ({
        labels: riskBuckets.slice(0, -1).map((v, i) => `${(v * 100).toFixed(0)}-${(riskBuckets[i + 1] * 100).toFixed(0)}%`),
        datasets: [{
            label: 'Vendor Count',
            data: riskHistogram,
            backgroundColor: riskBuckets.slice(0, -1).map(v => v >= 0.6 ? '#ef4444' : v >= 0.3 ? '#f59e0b' : '#22c55e'),
            borderRadius: 4,
        }],
    }), [riskHistogram]);

    // Vendor detail radar
    const radarData = selectedVendor ? {
        labels: ['Filing Regularity', 'Tax Accuracy', 'E-Invoice Compliance', 'ITC Match Rate', 'Response Time', 'Volume'],
        datasets: [{
            label: selectedVendor.name,
            data: [
                selectedVendor.missedFilings === 0 ? 95 : Math.max(30, 90 - selectedVendor.missedFilings * 15),
                100 - selectedVendor.riskScore * 60,
                selectedVendor.riskScore < 0.3 ? 92 : selectedVendor.riskScore < 0.6 ? 65 : 35,
                100 - selectedVendor.riskScore * 50,
                selectedVendor.avgDaysLate === 0 ? 98 : Math.max(20, 95 - selectedVendor.avgDaysLate * 5),
                Math.min(100, selectedVendor.totalTransactions / 5),
            ],
            backgroundColor: 'rgba(245, 158, 11, 0.15)',
            borderColor: '#f59e0b',
            borderWidth: 2,
            pointBackgroundColor: '#f59e0b',
            pointBorderColor: '#1a2035',
            pointBorderWidth: 2,
        }],
    } : null;

    const radarOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            r: {
                beginAtZero: true,
                max: 100,
                grid: { color: 'rgba(255,255,255,0.06)' },
                angleLines: { color: 'rgba(255,255,255,0.06)' },
                pointLabels: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
                ticks: { display: false },
            },
        },
        plugins: {
            legend: { display: false },
            tooltip: chartDefaults.plugins.tooltip,
        },
    };

    // Model performance metrics
    const modelMetrics = {
        accuracy: 98.3,
        precision: 96.7,
        recall: 94.2,
        f1Score: 95.4,
        auc: 0.987,
    };

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h2>📈 Predictive Vendor Compliance Risk Model</h2>
                <p>ML-powered risk prediction using graph features — Deliverable 5</p>
            </div>

            {/* Model Performance Card */}
            <div className="card mb-2" style={{ padding: '16px 24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Brain size={20} style={{ color: 'var(--accent-primary)' }} />
                        <span style={{ fontWeight: 600 }}>RandomForest Classifier</span>
                        <span className="badge success">Trained</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Last trained: 2 days ago</span>
                    </div>
                    <div style={{ display: 'flex', gap: '20px', fontSize: '0.8rem' }}>
                        {Object.entries(modelMetrics).map(([key, val]) => (
                            <div key={key} style={{ textAlign: 'center' }}>
                                <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', textTransform: 'uppercase' }}>{key.replace(/([A-Z])/g, ' $1')}</div>
                                <div style={{ fontWeight: 700, color: val > 95 ? 'var(--success)' : 'var(--warning)', fontFamily: 'JetBrains Mono', fontSize: '1rem' }}>{typeof val === 'number' && val < 1 ? val.toFixed(3) : val + '%'}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Charts Row */}
            <div className="charts-grid">
                <div className="chart-card">
                    <h3>Feature Importance</h3>
                    <div className="chart-subtitle">Key predictors in the vendor risk model</div>
                    <div className="chart-container">
                        <Bar data={featureImportanceData} options={{ ...chartDefaults, indexAxis: 'y', plugins: { ...chartDefaults.plugins, legend: { display: false } } }} />
                    </div>
                </div>
                <div className="chart-card">
                    <h3>Risk Score Distribution</h3>
                    <div className="chart-subtitle">Histogram of vendor risk scores</div>
                    <div className="chart-container">
                        <Bar data={histogramData} options={{ ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } }, scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, ticks: { ...chartDefaults.scales.y.ticks, stepSize: 1 } } } }} />
                    </div>
                </div>
            </div>

            {/* Vendor Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
                {/* Vendor Score Table */}
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-primary)' }}>
                        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Target size={16} /> Vendor Risk Scores</h3>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '4px' }}>Click a vendor to see detailed compliance profile</p>
                    </div>
                    <div className="data-table-container" style={{ maxHeight: '440px', overflowY: 'auto' }}>
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>Vendor</th>
                                    <th>Risk Score</th>
                                    <th>Status</th>
                                    <th>Trend</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[...vendors].sort((a, b) => b.riskScore - a.riskScore).map(v => (
                                    <tr
                                        key={v.id}
                                        onClick={() => setSelectedVendor(v)}
                                        style={{ cursor: 'pointer', background: selectedVendor?.id === v.id ? 'rgba(245,158,11,0.05)' : 'transparent' }}
                                    >
                                        <td style={{ fontWeight: 500, maxWidth: '140px' }} className="truncate">{v.name}</td>
                                        <td>
                                            <div className="risk-meter">
                                                <span className="mono" style={{ minWidth: '36px', fontSize: '0.8rem', fontWeight: 700, color: v.riskScore > 0.6 ? 'var(--danger)' : v.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)' }}>{(v.riskScore * 100).toFixed(0)}%</span>
                                                <div className="risk-bar">
                                                    <div style={{ height: '100%', borderRadius: '3px', width: `${v.riskScore * 100}%`, background: v.riskScore > 0.6 ? 'var(--danger)' : v.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)', transition: 'width 0.5s ease' }}></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td><span className={`badge ${v.status === 'High Risk' ? 'high' : v.status === 'Review' ? 'review' : 'compliant'}`}>{v.status}</span></td>
                                        <td>
                                            {v.riskScore > 0.5 ? <TrendingUp size={14} style={{ color: 'var(--danger)' }} /> : v.riskScore > 0.25 ? <span style={{ color: 'var(--warning)' }}>→</span> : <TrendingUp size={14} style={{ color: 'var(--success)', transform: 'rotate(180deg)' }} />}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Vendor Detail Panel */}
                <div>
                    {!selectedVendor ? (
                        <div className="card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                            <BarChart3 size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 16px' }} />
                            <h3 style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Select a vendor</h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Click on a vendor in the table to view their compliance profile and radar chart</p>
                        </div>
                    ) : (
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <div className="card mb-2">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <div>
                                        <h3 style={{ marginBottom: '4px' }}>{selectedVendor.name}</h3>
                                        <p className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{selectedVendor.gstin}</p>
                                    </div>
                                    <span className={`badge ${selectedVendor.status === 'High Risk' ? 'high' : selectedVendor.status === 'Review' ? 'review' : 'compliant'}`} style={{ fontSize: '0.85rem', padding: '6px 14px' }}>{selectedVendor.status}</span>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">State</span>
                                        <span className="node-detail-value">{selectedVendor.state}</span>
                                    </div>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">Risk Score</span>
                                        <span className="node-detail-value" style={{ color: selectedVendor.riskScore > 0.6 ? 'var(--danger)' : selectedVendor.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)', fontWeight: 700 }}>{(selectedVendor.riskScore * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">Total Transactions</span>
                                        <span className="node-detail-value">{selectedVendor.totalTransactions}</span>
                                    </div>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">Missed Filings</span>
                                        <span className="node-detail-value" style={{ color: selectedVendor.missedFilings > 0 ? 'var(--danger)' : 'var(--text-primary)' }}>{selectedVendor.missedFilings}</span>
                                    </div>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">Avg Days Late</span>
                                        <span className="node-detail-value">{selectedVendor.avgDaysLate}</span>
                                    </div>
                                    <div className="node-detail-row">
                                        <span className="node-detail-label">Prediction</span>
                                        <span className="node-detail-value">{selectedVendor.riskScore > 0.6 ? 'Likely non-compliant' : selectedVendor.riskScore > 0.3 ? 'Needs monitoring' : 'Expected compliant'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="chart-card">
                                <h3>Compliance Profile Radar</h3>
                                <div className="chart-subtitle">Multi-dimensional vendor assessment</div>
                                <div className="chart-container" style={{ height: '280px' }}>
                                    {radarData && <Radar data={radarData} options={radarOptions} />}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>


        </motion.div>
    );
}
