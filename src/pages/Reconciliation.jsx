import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Download, AlertCircle, CheckCircle, XCircle, FileWarning } from 'lucide-react';
import { useData } from '../context/DataContext';

const statusIcons = {
    'Missing in GSTR-1': <XCircle size={14} />,
    'Tax Amount Mismatch': <AlertCircle size={14} />,
    'HSN Mismatch': <FileWarning size={14} />,
    'Late Filing': <AlertCircle size={14} />,
    'E-Way Bill Missing': <FileWarning size={14} />,
    'Matched': <CheckCircle size={14} />,
};

function formatINR(num) {
    return '₹' + num.toLocaleString('en-IN');
}

export default function Reconciliation() {
    const { invoices } = useData();
    const [periodFilter, setPeriodFilter] = useState('all');
    const [riskFilter, setRiskFilter] = useState('all');
    const [typeFilter, setTypeFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedInvoice, setSelectedInvoice] = useState(null);

    const filteredInvoices = useMemo(() => {
        return invoices.filter(inv => {
            if (periodFilter !== 'all' && inv.period !== periodFilter) return false;
            if (riskFilter !== 'all' && inv.riskLevel !== riskFilter) return false;
            if (typeFilter !== 'all' && inv.matchStatus !== typeFilter) return false;
            if (searchTerm && !inv.id.toLowerCase().includes(searchTerm.toLowerCase()) &&
                !inv.vendorName.toLowerCase().includes(searchTerm.toLowerCase())) return false;
            return true;
        });
    }, [invoices, periodFilter, riskFilter, typeFilter, searchTerm]);

    const mismatchSummary = useMemo(() => {
        const mm = filteredInvoices.filter(i => i.matchStatus !== 'Matched');
        return {
            total: mm.length,
            totalTax: mm.reduce((s, i) => s + i.totalTax, 0),
            highCount: mm.filter(i => i.riskLevel === 'High').length,
        };
    }, [filteredInvoices]);

    const periods = [...new Set(invoices.map(i => i.period))];
    const types = [...new Set(invoices.map(i => i.matchStatus))];

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h2>🔍 Reconciliation Engine</h2>
                <p>Graph-traversal mismatch detection with root-cause classification — Deliverable 2</p>
            </div>

            {/* Summary Cards */}
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="kpi-card red">
                    <div className="kpi-label">Mismatches Found</div>
                    <div className="kpi-value red">{mismatchSummary.total}</div>
                </div>
                <div className="kpi-card purple">
                    <div className="kpi-label">Total Tax at Risk</div>
                    <div className="kpi-value purple">{formatINR(mismatchSummary.totalTax)}</div>
                </div>
                <div className="kpi-card orange">
                    <div className="kpi-label">High Risk Cases</div>
                    <div className="kpi-value orange">{mismatchSummary.highCount}</div>
                </div>
            </div>

            {/* Filters */}
            <div className="filter-bar">
                <div style={{ position: 'relative', flex: '1', maxWidth: '300px' }}>
                    <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        className="filter-input"
                        style={{ paddingLeft: '36px', width: '100%' }}
                        placeholder="Search invoice or vendor..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <select className="filter-select" value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value)}>
                    <option value="all">All Periods</option>
                    {periods.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
                <select className="filter-select" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                    <option value="all">All Risk Levels</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                </select>
                <select className="filter-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                    <option value="all">All Types</option>
                    {types.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
            </div>

            {/* Table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div className="data-table-container" style={{ maxHeight: '520px', overflowY: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Invoice ID</th>
                                <th>Vendor</th>
                                <th>GSTIN</th>
                                <th>Date</th>
                                <th>Taxable Amt</th>
                                <th>Tax</th>
                                <th>HSN</th>
                                <th>GSTR-1</th>
                                <th>GSTR-2B</th>
                                <th>e-Invoice</th>
                                <th>Status</th>
                                <th>Risk</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredInvoices.map(inv => (
                                <tr
                                    key={inv.id}
                                    onClick={() => setSelectedInvoice(inv)}
                                    style={{ cursor: 'pointer', background: selectedInvoice?.id === inv.id ? 'rgba(245,158,11,0.05)' : 'transparent' }}
                                >
                                    <td className="mono" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{inv.id}</td>
                                    <td className="truncate" style={{ maxWidth: '140px' }}>{inv.vendorName}</td>
                                    <td className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{inv.gstin}</td>
                                    <td>{inv.date}</td>
                                    <td className="amount">{formatINR(inv.taxableAmount)}</td>
                                    <td className="amount">{formatINR(inv.totalTax)}</td>
                                    <td className="mono">{inv.hsn}</td>
                                    <td>{inv.gstr1Reported ? <span style={{ color: 'var(--success)' }}>✓</span> : <span style={{ color: 'var(--danger)' }}>✗</span>}</td>
                                    <td>{inv.gstr2bReported ? <span style={{ color: 'var(--success)' }}>✓</span> : <span style={{ color: 'var(--danger)' }}>✗</span>}</td>
                                    <td>{inv.eInvoice ? <span style={{ color: 'var(--success)' }}>✓</span> : <span style={{ color: 'var(--danger)' }}>✗</span>}</td>
                                    <td>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: inv.matchStatus === 'Matched' ? 'var(--success)' : 'var(--warning)' }}>
                                            {statusIcons[inv.matchStatus]}
                                            {inv.matchStatus}
                                        </span>
                                    </td>
                                    <td><span className={`badge ${inv.riskLevel.toLowerCase()}`}>{inv.riskLevel}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Selected Invoice Detail */}
            {selectedInvoice && selectedInvoice.matchStatus !== 'Matched' && (
                <motion.div
                    className="card mt-2"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h3 style={{ marginBottom: '16px' }}>📋 Mismatch Detail: {selectedInvoice.id}</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Invoice ID</span>
                                <span className="node-detail-value mono">{selectedInvoice.id}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Vendor</span>
                                <span className="node-detail-value">{selectedInvoice.vendorName}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">GSTIN</span>
                                <span className="node-detail-value mono">{selectedInvoice.gstin}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Taxable Amount</span>
                                <span className="node-detail-value amount">{formatINR(selectedInvoice.taxableAmount)}</span>
                            </div>
                        </div>
                        <div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Period</span>
                                <span className="node-detail-value">{selectedInvoice.period}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Issue Type</span>
                                <span className="node-detail-value" style={{ color: 'var(--danger)' }}>{selectedInvoice.matchStatus}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Tax at Risk</span>
                                <span className="node-detail-value amount" style={{ color: 'var(--danger)' }}>{formatINR(selectedInvoice.totalTax)}</span>
                            </div>
                            <div className="node-detail-row">
                                <span className="node-detail-label">Risk Level</span>
                                <span className="node-detail-value"><span className={`badge ${selectedInvoice.riskLevel.toLowerCase()}`}>{selectedInvoice.riskLevel}</span></span>
                            </div>
                        </div>
                    </div>
                    <div className="mt-2">
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px' }}>Graph Traversal Path (Cypher)</h4>
                        <pre className="audit-graph-path" style={{ whiteSpace: 'pre-wrap' }}>
                            {`MATCH (v:Vendor {gstin:'${selectedInvoice.gstin}'})-[:ISSUED_INVOICE]->(i:Invoice {id:'${selectedInvoice.id}'})
MATCH (i)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B', period:'${selectedInvoice.period}'})
WHERE NOT EXISTS {
  MATCH (i)-[:MATCHES]->(:Invoice)-[:REPORTED_IN]->(:GSTR {type:'GSTR-1', period:'${selectedInvoice.period}'})
}
RETURN v.name AS vendor, i.id AS invoice, i.tax_amount AS tax`}
                        </pre>
                    </div>
                </motion.div>
            )}
        </motion.div>
    );
}
