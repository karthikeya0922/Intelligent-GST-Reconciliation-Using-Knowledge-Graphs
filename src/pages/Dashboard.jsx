import { useState, useMemo } from 'react';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, FileWarning, Shield } from 'lucide-react';
import { useData } from '../context/DataContext';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler);

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, boxWidth: 12, padding: 16 } },
        tooltip: { backgroundColor: '#1a2035', borderColor: '#f59e0b22', borderWidth: 1, titleColor: '#f1f5f9', bodyColor: '#94a3b8', padding: 12, cornerRadius: 8, titleFont: { family: 'Inter', weight: '600' }, bodyFont: { family: 'Inter' } }
    },
    scales: {
        x: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } } }
    }
};

function formatINR(num) {
    if (num >= 10000000) return '₹' + (num / 10000000).toFixed(1) + ' Cr';
    if (num >= 100000) return '₹' + (num / 100000).toFixed(1) + ' L';
    if (num >= 1000) return '₹' + (num / 1000).toFixed(1) + 'K';
    return '₹' + num;
}

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } };

export default function Dashboard() {
    const { kpiData, monthlyITCRisk, mismatchTypes, alerts: recentAlerts, complianceTrend, vendors, invoices } = useData();
    const itcTrendData = useMemo(() => ({
        labels: monthlyITCRisk.map(d => d.month.split(' ')[0]),
        datasets: [
            {
                label: 'Total ITC Claimed',
                data: monthlyITCRisk.map(d => d.total),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#3b82f6',
            },
            {
                label: 'At-Risk ITC',
                data: monthlyITCRisk.map(d => d.atRisk),
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#ef4444',
            },
        ],
    }), [monthlyITCRisk]);

    const mismatchDonut = useMemo(() => ({
        labels: mismatchTypes.map(m => m.type),
        datasets: [{
            data: mismatchTypes.map(m => m.count),
            backgroundColor: mismatchTypes.map(m => m.color),
            borderColor: '#1a2035',
            borderWidth: 3,
            hoverOffset: 6,
        }],
    }), [mismatchTypes]);

    const complianceBar = useMemo(() => ({
        labels: complianceTrend.map(d => d.month),
        datasets: [
            { label: 'Compliant', data: complianceTrend.map(d => d.compliant), backgroundColor: '#22c55e', borderRadius: 4 },
            { label: 'Under Review', data: complianceTrend.map(d => d.review), backgroundColor: '#f59e0b', borderRadius: 4 },
            { label: 'High Risk', data: complianceTrend.map(d => d.highRisk), backgroundColor: '#ef4444', borderRadius: 4 },
        ],
    }), [complianceTrend]);

    return (
        <motion.div variants={container} initial="hidden" animate="show">
            <div className="page-header">
                <div className="page-header-row">
                    <div>
                        <h2>📊 Dashboard Overview</h2>
                        <p>Real-time GST reconciliation intelligence powered by Knowledge Graphs</p>
                    </div>
                    <div className="flex gap-1">
                        <span className="badge info">Period: Jul-Sep 2025</span>
                        <span className="badge success">● System Online</span>
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <motion.div className="kpi-grid" variants={container}>
                <motion.div className="kpi-card orange" variants={item}>
                    <div className="kpi-label">Total Invoices Processed</div>
                    <div className="kpi-value orange">{kpiData.totalInvoices}</div>
                    <div className="kpi-change up"><TrendingUp size={12} /> +12.4% from last quarter</div>
                </motion.div>
                <motion.div className="kpi-card red" variants={item}>
                    <div className="kpi-label">Mismatches Detected</div>
                    <div className="kpi-value red">{kpiData.totalMismatches}</div>
                    <div className="kpi-change down"><TrendingDown size={12} /> 5.8% mismatch rate</div>
                </motion.div>
                <motion.div className="kpi-card purple" variants={item}>
                    <div className="kpi-label">At-Risk ITC Amount</div>
                    <div className="kpi-value purple">{formatINR(kpiData.atRiskITC)}</div>
                    <div className="kpi-change down"><AlertTriangle size={12} /> Needs reconciliation</div>
                </motion.div>
                <motion.div className="kpi-card green" variants={item}>
                    <div className="kpi-label">Match Rate</div>
                    <div className="kpi-value green">{kpiData.matchRate}%</div>
                    <div className="kpi-change up"><CheckCircle size={12} /> Above 90% target</div>
                </motion.div>
                <motion.div className="kpi-card blue" variants={item}>
                    <div className="kpi-label">Vendors Monitored</div>
                    <div className="kpi-value blue">{kpiData.vendorsMonitored}</div>
                    <div className="kpi-change up"><Shield size={12} /> {kpiData.highRiskVendors} high risk</div>
                </motion.div>
                <motion.div className="kpi-card cyan" variants={item}>
                    <div className="kpi-label">Avg Resolution Time</div>
                    <div className="kpi-value cyan">{kpiData.avgResolutionDays} days</div>
                    <div className="kpi-change up"><TrendingUp size={12} /> Improved by 18%</div>
                </motion.div>
            </motion.div>

            {/* Charts Row */}
            <motion.div className="charts-grid" variants={item}>
                <div className="chart-card">
                    <h3>ITC Risk Trend</h3>
                    <div className="chart-subtitle">Monthly total vs. at-risk input tax credit</div>
                    <div className="chart-container">
                        <Line data={itcTrendData} options={{ ...chartDefaults, plugins: { ...chartDefaults.plugins, legend: { ...chartDefaults.plugins.legend, position: 'top' } } }} />
                    </div>
                </div>
                <div className="chart-card">
                    <h3>Mismatch Distribution</h3>
                    <div className="chart-subtitle">Breakdown by mismatch type</div>
                    <div className="chart-container" style={{ display: 'flex', justifyContent: 'center' }}>
                        <Doughnut data={mismatchDonut} options={{ ...chartDefaults, scales: {}, cutout: '65%', plugins: { ...chartDefaults.plugins, legend: { ...chartDefaults.plugins.legend, position: 'right' } } }} />
                    </div>
                </div>
            </motion.div>

            {/* Bottom Row */}
            <motion.div className="charts-grid" variants={item}>
                <div className="chart-card">
                    <h3>Vendor Compliance Trend</h3>
                    <div className="chart-subtitle">Monthly vendor status distribution (%)</div>
                    <div className="chart-container">
                        <Bar data={complianceBar} options={{ ...chartDefaults, scales: { ...chartDefaults.scales, x: { ...chartDefaults.scales.x, stacked: true }, y: { ...chartDefaults.scales.y, stacked: true, max: 100 } }, plugins: { ...chartDefaults.plugins, legend: { ...chartDefaults.plugins.legend, position: 'top' } } }} />
                    </div>
                </div>
                <div className="chart-card">
                    <h3>Recent Alerts</h3>
                    <div className="chart-subtitle">Latest system notifications</div>
                    <div className="alerts-list" style={{ maxHeight: '280px', overflowY: 'auto' }}>
                        {recentAlerts.map((alert, index) => (
                            <div key={index} className="alert-item">
                                <span className="alert-icon">{alert.icon}</span>
                                <div className="alert-content">
                                    <div className="alert-message">{alert.message}</div>
                                    <div className="alert-time">{alert.time}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}
