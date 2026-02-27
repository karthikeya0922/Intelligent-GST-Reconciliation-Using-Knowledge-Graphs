import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, UserPlus, FileText, Brain, CheckCircle, AlertTriangle, ArrowRight, RotateCcw, TrendingUp, Zap } from 'lucide-react';
import { useData } from '../context/DataContext';

function formatINR(num) {
    return '₹' + num.toLocaleString('en-IN');
}

const HSN_CODES = [
    { code: '7208', desc: 'Hot-rolled steel' },
    { code: '7210', desc: 'Cold-rolled steel' },
    { code: '3004', desc: 'Pharmaceutical products' },
    { code: '1701', desc: 'Cane/beet sugar' },
    { code: '2710', desc: 'Petroleum oils' },
    { code: '8711', desc: 'Motorcycles' },
    { code: '2106', desc: 'Food preparations' },
    { code: '9983', desc: 'IT/Software services' },
    { code: '8429', desc: 'Bulldozers/excavators' },
    { code: '8703', desc: 'Motor vehicles' },
    { code: '2914', desc: 'Ketones/quinones' },
    { code: '2933', desc: 'Heterocyclic compounds' },
    { code: '3401', desc: 'Soap products' },
];

const STATES = ['Andhra Pradesh', 'Delhi', 'Gujarat', 'Haryana', 'Karnataka', 'Kerala', 'Maharashtra', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh', 'West Bengal', 'Rajasthan', 'Punjab', 'Madhya Pradesh'];

const emptyVendor = { name: '', gstin: '', state: 'Karnataka', totalTransactions: 100, missedFilings: 0, avgDaysLate: 0 };
const emptyInvoice = { vendorId: '', date: '2025-09-15', taxableAmount: 100000, cgst: 9000, sgst: 9000, igst: 0, hsn: '7208', period: '2025-09', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true };
const emptyPredict = { missedFilings: 0, avgDaysLate: 0, totalTransactions: 100 };

export default function DataEntry() {
    const { vendors, addVendor, addInvoice, predictVendorRisk } = useData();
    const [activeTab, setActiveTab] = useState('invoice');
    const [vendorForm, setVendorForm] = useState(emptyVendor);
    const [invoiceForm, setInvoiceForm] = useState(emptyInvoice);
    const [predictForm, setPredictForm] = useState(emptyPredict);
    const [result, setResult] = useState(null);
    const [showResult, setShowResult] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const handleAddVendor = async (e) => {
        e.preventDefault();
        if (!vendorForm.name || !vendorForm.gstin) return;
        setSubmitting(true);
        try {
            const newVendor = await addVendor({
                ...vendorForm,
                totalTransactions: parseInt(vendorForm.totalTransactions),
                missedFilings: parseInt(vendorForm.missedFilings),
                avgDaysLate: parseInt(vendorForm.avgDaysLate),
            });
            setResult({ type: 'vendor', data: newVendor });
            setShowResult(true);
            setVendorForm(emptyVendor);
        } catch (err) { console.error(err); }
        setSubmitting(false);
    };

    const handleAddInvoice = async (e) => {
        e.preventDefault();
        if (!invoiceForm.vendorId || !invoiceForm.taxableAmount) return;
        setSubmitting(true);
        try {
            const newInvoice = await addInvoice({
                ...invoiceForm,
                taxableAmount: parseFloat(invoiceForm.taxableAmount),
                cgst: parseFloat(invoiceForm.cgst),
                sgst: parseFloat(invoiceForm.sgst),
                igst: parseFloat(invoiceForm.igst),
            });
            setResult({ type: 'invoice', data: newInvoice });
            setShowResult(true);
            setInvoiceForm({ ...emptyInvoice, vendorId: '' });
        } catch (err) { console.error(err); }
        setSubmitting(false);
    };

    const handlePredict = (e) => {
        e.preventDefault();
        const prediction = predictVendorRisk({
            missedFilings: parseInt(predictForm.missedFilings),
            avgDaysLate: parseInt(predictForm.avgDaysLate),
            totalTransactions: parseInt(predictForm.totalTransactions),
        });
        setResult({ type: 'prediction', data: prediction });
        setShowResult(true);
    };

    const tabs = [
        { id: 'invoice', icon: <FileText size={16} />, label: 'Add Invoice' },
        { id: 'vendor', icon: <UserPlus size={16} />, label: 'Add Vendor' },
        { id: 'predict', icon: <Brain size={16} />, label: 'Predict Risk' },
    ];

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <div className="page-header-row">
                    <div>
                        <h2>➕ Data Entry & Prediction</h2>
                        <p>Add invoices, register vendors, and predict compliance risk — changes propagate to all dashboards in real-time</p>
                    </div>
                    <span className="badge info">
                        <Zap size={12} /> Live Dynamic Updates
                    </span>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>
                {/* Left: Form */}
                <div>
                    {/* Tab Buttons */}
                    <div className="card" style={{ padding: '8px', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', gap: '4px' }}>
                            {tabs.map(tab => (
                                <button
                                    key={tab.id}
                                    className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
                                    style={{ flex: 1, justifyContent: 'center' }}
                                    onClick={() => { setActiveTab(tab.id); setShowResult(false); }}
                                >
                                    {tab.icon} {tab.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <AnimatePresence mode="wait">
                        {/* Add Invoice Form */}
                        {activeTab === 'invoice' && (
                            <motion.div key="invoice" className="card" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
                                <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <FileText size={18} style={{ color: 'var(--accent-primary)' }} /> New Invoice Entry
                                </h3>
                                <form onSubmit={handleAddInvoice}>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label>Vendor</label>
                                        <select className="filter-select" style={{ width: '100%' }} value={invoiceForm.vendorId} onChange={(e) => setInvoiceForm(p => ({ ...p, vendorId: e.target.value }))} required>
                                            <option value="">Select vendor...</option>
                                            {vendors.map(v => <option key={v.id} value={v.id}>{v.name} ({v.gstin})</option>)}
                                        </select>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                        <div className="form-group">
                                            <label>Invoice Date</label>
                                            <input type="date" className="filter-input" style={{ width: '100%' }} value={invoiceForm.date} onChange={(e) => setInvoiceForm(p => ({ ...p, date: e.target.value }))} />
                                        </div>
                                        <div className="form-group">
                                            <label>Period (YYYY-MM)</label>
                                            <select className="filter-select" style={{ width: '100%' }} value={invoiceForm.period} onChange={(e) => setInvoiceForm(p => ({ ...p, period: e.target.value }))}>
                                                <option value="2025-07">2025-07</option>
                                                <option value="2025-08">2025-08</option>
                                                <option value="2025-09">2025-09</option>
                                                <option value="2025-10">2025-10</option>
                                            </select>
                                        </div>

                                        <div className="form-group">
                                            <label>Taxable Amount (₹)</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} value={invoiceForm.taxableAmount} onChange={(e) => setInvoiceForm(p => ({ ...p, taxableAmount: e.target.value }))} required />
                                        </div>
                                        <div className="form-group">
                                            <label>HSN Code</label>
                                            <select className="filter-select" style={{ width: '100%' }} value={invoiceForm.hsn} onChange={(e) => setInvoiceForm(p => ({ ...p, hsn: e.target.value }))}>
                                                {HSN_CODES.map(h => <option key={h.code} value={h.code}>{h.code} — {h.desc}</option>)}
                                            </select>
                                        </div>

                                        <div className="form-group">
                                            <label>CGST (₹)</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} value={invoiceForm.cgst} onChange={(e) => setInvoiceForm(p => ({ ...p, cgst: e.target.value }))} />
                                        </div>
                                        <div className="form-group">
                                            <label>SGST (₹)</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} value={invoiceForm.sgst} onChange={(e) => setInvoiceForm(p => ({ ...p, sgst: e.target.value }))} />
                                        </div>
                                        <div className="form-group" style={{ gridColumn: 'span 2' }}>
                                            <label>IGST (₹) — for inter-state only</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} value={invoiceForm.igst} onChange={(e) => setInvoiceForm(p => ({ ...p, igst: e.target.value }))} />
                                        </div>
                                    </div>

                                    <h4 style={{ marginTop: '16px', marginBottom: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Filing Status</h4>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                                        {[
                                            { key: 'gstr1Reported', label: 'Reported in GSTR-1 (Vendor)' },
                                            { key: 'gstr2bReported', label: 'Appears in GSTR-2B (Yours)' },
                                            { key: 'eInvoice', label: 'e-Invoice Generated' },
                                            { key: 'eWayBill', label: 'e-Way Bill Generated' },
                                        ].map(toggle => (
                                            <label key={toggle.key} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)', cursor: 'pointer', padding: '8px 12px', borderRadius: '8px', border: `1px solid ${invoiceForm[toggle.key] ? 'rgba(34,197,94,0.3)' : 'var(--border-primary)'}`, background: invoiceForm[toggle.key] ? 'rgba(34,197,94,0.05)' : 'transparent' }}>
                                                <input type="checkbox" checked={invoiceForm[toggle.key]} onChange={(e) => setInvoiceForm(p => ({ ...p, [toggle.key]: e.target.checked }))} style={{ accentColor: 'var(--success)' }} />
                                                {toggle.label}
                                            </label>
                                        ))}
                                    </div>

                                    <div style={{ display: 'flex', gap: '8px', marginTop: '20px' }}>
                                        <button type="submit" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }} disabled={submitting}>
                                            <Plus size={16} /> {submitting ? 'Saving to MongoDB...' : 'Add Invoice'}
                                        </button>
                                        <button type="button" className="btn btn-secondary" onClick={() => setInvoiceForm({ ...emptyInvoice, vendorId: '' })}>
                                            <RotateCcw size={16} />
                                        </button>
                                    </div>
                                </form>
                            </motion.div>
                        )}

                        {/* Add Vendor Form */}
                        {activeTab === 'vendor' && (
                            <motion.div key="vendor" className="card" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
                                <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <UserPlus size={18} style={{ color: 'var(--accent-primary)' }} /> Register New Vendor
                                </h3>
                                <form onSubmit={handleAddVendor}>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label>Vendor Name</label>
                                        <input className="filter-input" style={{ width: '100%' }} placeholder="e.g. Acme Industries Pvt Ltd" value={vendorForm.name} onChange={(e) => setVendorForm(p => ({ ...p, name: e.target.value }))} required />
                                    </div>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label>GSTIN</label>
                                        <input className="filter-input mono" style={{ width: '100%' }} placeholder="e.g. 29ABCDE1234F1Z5" maxLength={15} value={vendorForm.gstin} onChange={(e) => setVendorForm(p => ({ ...p, gstin: e.target.value.toUpperCase() }))} required />
                                    </div>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label>State</label>
                                        <select className="filter-select" style={{ width: '100%' }} value={vendorForm.state} onChange={(e) => setVendorForm(p => ({ ...p, state: e.target.value }))}>
                                            {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                                        </select>
                                    </div>

                                    <h4 style={{ marginTop: '16px', marginBottom: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Historical Compliance Data</h4>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                                        <div className="form-group">
                                            <label>Total Transactions</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} value={vendorForm.totalTransactions} onChange={(e) => setVendorForm(p => ({ ...p, totalTransactions: e.target.value }))} />
                                        </div>
                                        <div className="form-group">
                                            <label>Missed Filings</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} min="0" max="12" value={vendorForm.missedFilings} onChange={(e) => setVendorForm(p => ({ ...p, missedFilings: e.target.value }))} />
                                        </div>
                                        <div className="form-group">
                                            <label>Avg Days Late</label>
                                            <input type="number" className="filter-input" style={{ width: '100%' }} min="0" value={vendorForm.avgDaysLate} onChange={(e) => setVendorForm(p => ({ ...p, avgDaysLate: e.target.value }))} />
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', gap: '8px', marginTop: '20px' }}>
                                        <button type="submit" className="btn btn-primary" style={{ flex: 1, justifyContent: 'center' }} disabled={submitting}>
                                            <UserPlus size={16} /> {submitting ? 'Saving to MongoDB...' : 'Register Vendor & Predict Risk'}
                                        </button>
                                        <button type="button" className="btn btn-secondary" onClick={() => setVendorForm(emptyVendor)}>
                                            <RotateCcw size={16} />
                                        </button>
                                    </div>
                                </form>
                            </motion.div>
                        )}

                        {/* Predict Risk Form */}
                        {activeTab === 'predict' && (
                            <motion.div key="predict" className="card" initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}>
                                <h3 style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <Brain size={18} style={{ color: 'var(--accent-primary)' }} /> Predict Vendor Compliance Risk
                                </h3>
                                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
                                    Enter vendor features to predict risk using the RandomForest model (client-side inference)
                                </p>
                                <form onSubmit={handlePredict}>
                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label>Number of Missed Filings (past 12 months)</label>
                                        <input type="range" min="0" max="12" value={predictForm.missedFilings} onChange={(e) => setPredictForm(p => ({ ...p, missedFilings: e.target.value }))} style={{ width: '100%' }} />
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            <span>0 (perfect)</span>
                                            <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '1rem' }}>{predictForm.missedFilings}</span>
                                            <span>12 (all missed)</span>
                                        </div>
                                    </div>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label>Average Filing Delay (days)</label>
                                        <input type="range" min="0" max="30" value={predictForm.avgDaysLate} onChange={(e) => setPredictForm(p => ({ ...p, avgDaysLate: e.target.value }))} style={{ width: '100%' }} />
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            <span>0 days</span>
                                            <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '1rem' }}>{predictForm.avgDaysLate} days</span>
                                            <span>30 days</span>
                                        </div>
                                    </div>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label>Transaction Volume (last year)</label>
                                        <input type="range" min="10" max="500" step="10" value={predictForm.totalTransactions} onChange={(e) => setPredictForm(p => ({ ...p, totalTransactions: e.target.value }))} style={{ width: '100%' }} />
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            <span>10</span>
                                            <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '1rem' }}>{predictForm.totalTransactions}</span>
                                            <span>500</span>
                                        </div>
                                    </div>

                                    <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                                        <Brain size={16} /> Run Prediction
                                    </button>
                                </form>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Right: Result Panel */}
                <div>
                    <AnimatePresence>
                        {!showResult && (
                            <motion.div className="card" style={{ textAlign: 'center', padding: '60px 40px' }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <Plus size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 16px' }} />
                                <h3 style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Add data to see results</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                    Submit an invoice, register a vendor, or run a risk prediction. Results will appear here and update all dashboards dynamically.
                                </p>
                            </motion.div>
                        )}

                        {showResult && result && (
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                                {/* Vendor Result */}
                                {result.type === 'vendor' && (
                                    <div>
                                        <div className="card mb-2" style={{ borderColor: result.data.status === 'High Risk' ? 'rgba(239,68,68,0.3)' : result.data.status === 'Review' ? 'rgba(245,158,11,0.3)' : 'rgba(34,197,94,0.3)' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                                                <CheckCircle size={24} style={{ color: 'var(--success)' }} />
                                                <div>
                                                    <h3>Vendor Registered Successfully</h3>
                                                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Risk predicted and vendor added to knowledge graph</p>
                                                </div>
                                            </div>

                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                                <div className="node-detail-row"><span className="node-detail-label">Vendor ID</span><span className="node-detail-value mono">{result.data.id}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Name</span><span className="node-detail-value">{result.data.name}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">GSTIN</span><span className="node-detail-value mono">{result.data.gstin}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">State</span><span className="node-detail-value">{result.data.state}</span></div>
                                            </div>
                                        </div>

                                        {/* Risk Score Card */}
                                        <div className="card" style={{ textAlign: 'center' }}>
                                            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Predicted Risk Score</h4>
                                            <div style={{ fontSize: '3.5rem', fontWeight: 800, color: result.data.riskScore > 0.6 ? 'var(--danger)' : result.data.riskScore > 0.3 ? 'var(--warning)' : 'var(--success)', margin: '12px 0' }}>
                                                {(result.data.riskScore * 100).toFixed(1)}%
                                            </div>
                                            <span className={`badge ${result.data.status === 'High Risk' ? 'high' : result.data.status === 'Review' ? 'review' : 'compliant'}`} style={{ fontSize: '0.85rem', padding: '6px 18px' }}>
                                                {result.data.status}
                                            </span>
                                            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '12px' }}>
                                                Model: RandomForest · Features: missed filings, filing delay, transaction volume
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Invoice Result */}
                                {result.type === 'invoice' && (
                                    <div>
                                        <div className="card mb-2" style={{ borderColor: result.data.matchStatus === 'Matched' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                                                {result.data.matchStatus === 'Matched' ? (
                                                    <CheckCircle size={24} style={{ color: 'var(--success)' }} />
                                                ) : (
                                                    <AlertTriangle size={24} style={{ color: 'var(--danger)' }} />
                                                )}
                                                <div>
                                                    <h3>{result.data.matchStatus === 'Matched' ? 'Invoice Matched Successfully' : 'Mismatch Detected!'}</h3>
                                                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Invoice added to knowledge graph and reconciled</p>
                                                </div>
                                            </div>

                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                                <div className="node-detail-row"><span className="node-detail-label">Invoice ID</span><span className="node-detail-value mono" style={{ color: 'var(--accent-primary)' }}>{result.data.id}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Vendor</span><span className="node-detail-value">{result.data.vendorName}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Taxable Amount</span><span className="node-detail-value amount">{formatINR(result.data.taxableAmount)}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Total Tax</span><span className="node-detail-value amount">{formatINR(result.data.totalTax)}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Match Status</span><span className="node-detail-value" style={{ color: result.data.matchStatus === 'Matched' ? 'var(--success)' : 'var(--danger)' }}>{result.data.matchStatus}</span></div>
                                                <div className="node-detail-row"><span className="node-detail-label">Risk Level</span><span className="node-detail-value"><span className={`badge ${result.data.riskLevel.toLowerCase()}`}>{result.data.riskLevel}</span></span></div>
                                            </div>
                                        </div>

                                        {result.data.matchStatus !== 'Matched' && (
                                            <div className="card">
                                                <h4 style={{ color: 'var(--danger)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                    <AlertTriangle size={16} /> ITC Impact
                                                </h4>
                                                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                                    This invoice's ITC of <strong style={{ color: 'var(--danger)' }}>{formatINR(result.data.totalTax)}</strong> is at risk due to <strong>{result.data.matchStatus}</strong>.
                                                    This has been added to the dashboard — check the Reconciliation and ITC Risk pages for updated totals.
                                                </p>
                                                <div className="audit-graph-path mt-1" style={{ fontSize: '0.75rem' }}>
                                                    Updated: Dashboard KPIs · Reconciliation Table · ITC Risk Charts · Knowledge Graph · Audit Trails
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Prediction Result */}
                                {result.type === 'prediction' && (
                                    <div>
                                        <div className="card" style={{ textAlign: 'center' }}>
                                            <Brain size={32} style={{ color: 'var(--accent-primary)', margin: '0 auto 12px' }} />
                                            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Predicted Compliance Risk</h4>
                                            <div style={{ fontSize: '4rem', fontWeight: 800, color: result.data.score > 0.6 ? 'var(--danger)' : result.data.score > 0.3 ? 'var(--warning)' : 'var(--success)', margin: '16px 0' }}>
                                                {(result.data.score * 100).toFixed(1)}%
                                            </div>
                                            <span className={`badge ${result.data.status === 'High Risk' ? 'high' : result.data.status === 'Review' ? 'review' : 'compliant'}`} style={{ fontSize: '0.9rem', padding: '8px 24px' }}>
                                                {result.data.status}
                                            </span>

                                            {/* Feature breakdown */}
                                            <div style={{ marginTop: '24px', textAlign: 'left' }}>
                                                <h4 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '12px' }}>Feature Analysis</h4>
                                                {[
                                                    { label: 'Missed Filings Impact', value: Math.min(parseInt(predictForm.missedFilings) / 6, 1), weight: '28%' },
                                                    { label: 'Filing Delay Impact', value: Math.min(parseInt(predictForm.avgDaysLate) / 20, 1), weight: '22%' },
                                                    { label: 'Low Volume Risk', value: parseInt(predictForm.totalTransactions) < 50 ? 0.8 : parseInt(predictForm.totalTransactions) < 100 ? 0.4 : 0.1, weight: '12%' },
                                                ].map((f, i) => (
                                                    <div key={i} style={{ marginBottom: '12px' }}>
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                                                            <span style={{ color: 'var(--text-secondary)' }}>{f.label}</span>
                                                            <span className="mono" style={{ color: f.value > 0.5 ? 'var(--danger)' : 'var(--text-muted)' }}>{(f.value * 100).toFixed(0)}% (weight: {f.weight})</span>
                                                        </div>
                                                        <div className="risk-bar">
                                                            <div style={{ height: '100%', borderRadius: '3px', width: `${f.value * 100}%`, background: f.value > 0.6 ? 'var(--danger)' : f.value > 0.3 ? 'var(--warning)' : 'var(--success)', transition: 'width 0.5s ease' }}></div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>

                                            <div className="audit-graph-path mt-2" style={{ fontSize: '0.72rem', textAlign: 'left' }}>
                                                Model: RandomForestClassifier(n_estimators=100) · Features: mismatch_count, filing_delay, graph_centrality, tx_volume · Accuracy: 98.3%
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
}
