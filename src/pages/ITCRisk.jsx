import { useMemo } from 'react';
import { Bar, Line, Pie } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { motion } from 'framer-motion';
import { ShieldAlert, TrendingUp, AlertTriangle } from 'lucide-react';
import { useData } from '../context/DataContext';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

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

function formatINR(num) {
    if (num >= 10000000) return '₹' + (num / 10000000).toFixed(1) + ' Cr';
    if (num >= 100000) return '₹' + (num / 100000).toFixed(1) + ' L';
    return '₹' + num.toLocaleString('en-IN');
}

export default function ITCRisk() {
    const { vendors, mismatches, monthlyITCRisk } = useData();
    const vendorRisk = useMemo(() => vendors
        .filter(v => v.riskScore > 0.3)
        .sort((a, b) => b.riskScore - a.riskScore)
        .slice(0, 10), [vendors]);

    const vendorMismatchAmounts = useMemo(() => vendorRisk.map(v => {
        const vendorMismatches = mismatches.filter(m => m.vendorId === v.id);
        return vendorMismatches.reduce((s, m) => s + m.totalTax, 0);
    }), [vendorRisk, mismatches]);

    const topVendorsData = useMemo(() => ({
        labels: vendorRisk.map(v => v.name.substring(0, 15)),
        datasets: [{
            label: 'At-Risk ITC (₹)',
            data: vendorMismatchAmounts,
            backgroundColor: vendorRisk.map(v => v.riskScore > 0.6 ? '#ef4444' : v.riskScore > 0.4 ? '#f59e0b' : '#3b82f6'),
            borderRadius: 6,
            borderSkipped: false,
        }],
    }), [vendorRisk, vendorMismatchAmounts]);

    const riskDistribution = useMemo(() => ({
        labels: ['Compliant', 'Under Review', 'High Risk'],
        datasets: [{
            data: [
                vendors.filter(v => v.status === 'Compliant').length,
                vendors.filter(v => v.status === 'Review').length,
                vendors.filter(v => v.status === 'High Risk').length,
            ],
            backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
            borderColor: '#1a2035',
            borderWidth: 3,
        }],
    }), [vendors]);

    const itcTrend = useMemo(() => ({
        labels: monthlyITCRisk.map(d => d.month.split(' ')[0]),
        datasets: [
            { label: 'Blocked ITC', data: monthlyITCRisk.map(d => d.atRisk), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.4, pointRadius: 4, pointBackgroundColor: '#ef4444' },
        ],
    }), [monthlyITCRisk]);

    const totalAtRisk = useMemo(() => mismatches.reduce((s, m) => s + m.totalTax, 0), [mismatches]);
    const highRiskVendors = useMemo(() => vendors.filter(v => v.status === 'High Risk'), [vendors]);

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h2>🛡️ ITC Risk Dashboard</h2>
                <p>Interactive ITC risk and vendor compliance scoring — Deliverable 3</p>
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                <div className="kpi-card red">
                    <div className="kpi-label">Total ITC at Risk</div>
                    <div className="kpi-value red">{formatINR(totalAtRisk)}</div>
                </div>
                <div className="kpi-card orange">
                    <div className="kpi-label">High Risk Vendors</div>
                    <div className="kpi-value orange">{highRiskVendors.length}</div>
                </div>
                <div className="kpi-card green">
                    <div className="kpi-label">Compliant Vendors</div>
                    <div className="kpi-value green">{vendors.filter(v => v.status === 'Compliant').length}</div>
                </div>
                <div className="kpi-card purple">
                    <div className="kpi-label">Avg Risk Score</div>
                    <div className="kpi-value purple">{(vendors.reduce((s, v) => s + v.riskScore, 0) / vendors.length * 100).toFixed(0)}%</div>
                </div>
            </div>

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-card">
                    <h3>Top Vendors by At-Risk ITC</h3>
                    <div className="chart-subtitle">Vendors with highest unmatched tax claims</div>
                    <div className="chart-container">
                        <Bar data={topVendorsData} options={{ ...chartDefaults, indexAxis: 'y', plugins: { ...chartDefaults.plugins, legend: { display: false } }, scales: { ...chartDefaults.scales, x: { ...chartDefaults.scales.x, ticks: { ...chartDefaults.scales.x.ticks, callback: (v) => '₹' + (v / 1000) + 'K' } } } }} />
                    </div>
                </div>
                <div className="chart-card">
                    <h3>Risk Distribution</h3>
                    <div className="chart-subtitle">Vendor compliance status breakdown</div>
                    <div className="chart-container" style={{ display: 'flex', justifyContent: 'center' }}>
                        <Pie data={riskDistribution} options={{ ...chartDefaults, scales: {}, plugins: { ...chartDefaults.plugins, legend: { ...chartDefaults.plugins.legend, position: 'right' } } }} />
                    </div>
                </div>
            </div>

            <div className="charts-grid" style={{ gridTemplateColumns: '1fr' }}>
                <div className="chart-card">
                    <h3>ITC Blocked Trend</h3>
                    <div className="chart-subtitle">Monthly blocked input tax credit due to mismatches</div>
                    <div className="chart-container" style={{ height: '240px' }}>
                        <Line data={itcTrend} options={{ ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { display: false } }, scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, ticks: { ...chartDefaults.scales.y.ticks, callback: (v) => '₹' + (v / 100000) + 'L' } } } }} />
                    </div>
                </div>
            </div>

            {/* Vendor Scorecard Table */}
            <div className="card mt-2" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-primary)' }}>
                    <h3>Vendor Compliance Scorecard</h3>
                </div>
                <div className="data-table-container" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Vendor</th>
                                <th>GSTIN</th>
                                <th>State</th>
                                <th>Risk Score</th>
                                <th>Status</th>
                                <th>Transactions</th>
                                <th>Missed Filings</th>
                                <th>Avg Days Late</th>
                            </tr>
                        </thead>
                        <tbody>
                            {[...vendors].sort((a, b) => b.riskScore - a.riskScore).map(v => (
                                <tr key={v.id}>
                                    <td style={{ fontWeight: 600 }}>{v.name}</td>
                                    <td className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{v.gstin}</td>
                                    <td>{v.state}</td>
                                    <td>
                                        <div className="risk-meter">
                                            <span className="mono" style={{ minWidth: '36px', fontSize: '0.8rem', fontWeight: 600, color: v.riskScore > 0.6 ? 'var(--danger)' : v.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)' }}>{(v.riskScore * 100).toFixed(0)}%</span>
                                            <div className="risk-bar">
                                                <div className="risk-fill" style={{ width: `${v.riskScore * 100}%`, background: v.riskScore > 0.6 ? 'var(--danger)' : v.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)' }}></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td><span className={`badge ${v.status === 'High Risk' ? 'high' : v.status === 'Review' ? 'review' : 'compliant'}`}>{v.status}</span></td>
                                    <td className="text-center">{v.totalTransactions}</td>
                                    <td className="text-center" style={{ color: v.missedFilings > 0 ? 'var(--danger)' : 'var(--text-muted)' }}>{v.missedFilings}</td>
                                    <td className="text-center" style={{ color: v.avgDaysLate > 5 ? 'var(--danger)' : 'var(--text-muted)' }}>{v.avgDaysLate}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </motion.div>
    );
}
