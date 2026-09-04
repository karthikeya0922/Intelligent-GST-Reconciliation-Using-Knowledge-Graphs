import { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import {
    monthlyITCRisk, mismatchTypes as defaultMismatchTypes,
    gstrReturns, riskFeatureImportance, auditExplanations as defaultAuditExplanations,
    complianceTrend
} from '../data/mockData';

const DataContext = createContext();

const API = 'http://localhost:8000/api';

// Offline-only risk heuristic. The authoritative score comes from the trained
// RandomForest behind POST /api/predict-risk; this mirrors the backend's own
// fallback (heuristic_risk in main.py) and is used only when the API is down.
function predictRisk(vendor) {
    const missed = Math.min((vendor.missedFilings || 0) / 6, 1);
    const late = Math.min((vendor.avgDaysLate || 0) / 20, 1);
    const tx = vendor.totalTransactions || 100;
    const txScore = tx < 50 ? 0.8 : tx < 100 ? 0.4 : 0.1;
    const einv = (vendor.missedFilings || 0) > 2 ? 0.7 : 0.2;
    return Math.min(Math.max(missed * 0.34 + late * 0.28 + txScore * 0.18 + einv * 0.20, 0.05), 0.95);
}

function classifyRisk(score) {
    if (score >= 0.6) return 'High Risk';
    if (score >= 0.3) return 'Review';
    return 'Compliant';
}

export function DataProvider({ children }) {
    const [vendors, setVendors] = useState([]);
    const [invoices, setInvoices] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [auditExplanations, setAuditExplanations] = useState(defaultAuditExplanations);
    const [loading, setLoading] = useState(true);
    const [apiOnline, setApiOnline] = useState(false);
    const [modelInfo, setModelInfo] = useState(null);
    const [graphStatus, setGraphStatus] = useState({ connected: false, reason: 'not checked' });
    // Graph read back out of Neo4j. Null means unavailable — the client-side
    // projection below is used instead.
    const [neo4jGraph, setNeo4jGraph] = useState(null);

    // Fetch all data from MongoDB backend on mount
    const fetchAll = useCallback(async () => {
        try {
            const [vendorsRes, invoicesRes, alertsRes] = await Promise.all([
                fetch(`${API}/vendors`),
                fetch(`${API}/invoices`),
                fetch(`${API}/alerts`),
            ]);
            if (vendorsRes.ok && invoicesRes.ok && alertsRes.ok) {
                setVendors(await vendorsRes.json());
                setInvoices(await invoicesRes.json());
                setAlerts(await alertsRes.json());
                setApiOnline(true);

                // Report what is really scoring vendors and whether the graph is up,
                // rather than asserting it in static UI copy.
                fetch(`${API}/model/info`)
                    .then(r => r.ok && r.json())
                    .then(info => info && setModelInfo(info))
                    .catch(() => setModelInfo(null));
                fetch(`${API}/graph/status`)
                    .then(r => r.ok && r.json())
                    .then(s => s && setGraphStatus(s))
                    .catch(() => setGraphStatus({ connected: false, reason: 'API unreachable' }));
                fetch(`${API}/graph/data`)
                    .then(r => r.ok && r.json())
                    .then(g => setNeo4jGraph(g && g.available ? g : null))
                    .catch(() => setNeo4jGraph(null));
            }
        } catch (err) {
            console.warn('API offline, using local mock data');
            // Fallback: import mock data
            const mock = await import('../data/mockData');
            setVendors(mock.vendors);
            setInvoices(mock.invoices);
            setAlerts(mock.recentAlerts);
            setApiOnline(false);
        }
        setLoading(false);
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    // Derived data
    const mismatches = useMemo(() => invoices.filter(inv => inv.matchStatus !== 'Matched'), [invoices]);

    const mismatchTypes = useMemo(() => {
        const typeMap = {};
        const colors = {
            'Missing in GSTR-1': '#ef4444', 'Tax Amount Mismatch': '#f59e0b',
            'HSN Mismatch': '#8b5cf6', 'Late Filing': '#3b82f6',
            'E-Way Bill Missing': '#06b6d4', 'Missing in GSTR-2B': '#ec4899',
        };
        mismatches.forEach(m => {
            if (!typeMap[m.matchStatus]) typeMap[m.matchStatus] = { type: m.matchStatus, count: 0, totalTax: 0, color: colors[m.matchStatus] || '#6366f1' };
            typeMap[m.matchStatus].count++;
            typeMap[m.matchStatus].totalTax += m.totalTax;
        });
        return Object.values(typeMap);
    }, [mismatches]);

    const kpiData = useMemo(() => {
        const totalMismatches = mismatches.length;
        const atRiskITC = mismatches.reduce((s, m) => s + m.totalTax, 0);
        const matchRate = invoices.length > 0 ? ((invoices.length - totalMismatches) / invoices.length * 100).toFixed(1) : 0;
        const highRiskVendors = vendors.filter(v => v.status === 'High Risk').length;
        return {
            totalInvoices: invoices.length, totalMismatches, atRiskITC,
            vendorsMonitored: vendors.length, matchRate: parseFloat(matchRate),
            avgResolutionDays: 4.2, highRiskVendors,
        };
    }, [invoices, mismatches, vendors]);

    // Client-side projection of the graph, built from the flat MongoDB rows.
    // Used when Neo4j is unavailable; otherwise `graphData` below prefers the
    // real graph read back out of the database.
    const localGraphData = useMemo(() => {
        const nodes = []; const links = [];
        const addedVendors = new Set(); const addedGstrs = new Set();

        // Add ALL vendors
        vendors.forEach(v => {
            nodes.push({ id: `v-${v.id}`, label: v.name.length > 14 ? v.name.substring(0, 13) + '…' : v.name, group: 'vendor', gstin: v.gstin, risk: v.riskScore, state: v.state, status: v.status });
            addedVendors.add(v.id);
        });

        // Add GSTR return nodes for each period
        const periods = [...new Set(invoices.map(i => i.period).filter(Boolean))];
        periods.forEach(p => {
            ['GSTR-1', 'GSTR-2B'].forEach(type => {
                const gId = `g-${type}-${p}`;
                if (!addedGstrs.has(gId)) {
                    const monthName = new Date(p + '-01').toLocaleString('en-IN', { month: 'short', year: '2-digit' });
                    nodes.push({ id: gId, label: `${type} ${monthName}`, group: 'gstr', type, period: p });
                    addedGstrs.add(gId);
                }
            });
        });

        // Add ALL invoices with full linking
        invoices.forEach(inv => {
            const invId = `i-${inv.id}`;
            nodes.push({ id: invId, label: inv.id.replace('INV-2025-', 'INV-'), group: 'invoice', amount: inv.total, matchStatus: inv.matchStatus, status: inv.matchStatus !== 'Matched' ? 'flagged' : 'matched' });

            // Vendor → Invoice
            if (addedVendors.has(inv.vendorId)) {
                links.push({ source: `v-${inv.vendorId}`, target: invId, label: 'ISSUED', type: 'issued' });
            }
            // Invoice → GSTR-2B
            if (inv.gstr2bReported && inv.period) {
                const g2Id = `g-GSTR-2B-${inv.period}`;
                if (addedGstrs.has(g2Id)) links.push({ source: invId, target: g2Id, label: 'IN_2B', type: 'reported' });
            }
            // Invoice → GSTR-1
            if (inv.gstr1Reported && inv.period) {
                const g1Id = `g-GSTR-1-${inv.period}`;
                if (addedGstrs.has(g1Id)) links.push({ source: invId, target: g1Id, label: 'IN_1', type: 'reported' });
            }
            // e-Invoice node
            if (inv.eInvoice) {
                const eId = `e-${inv.id}`;
                nodes.push({ id: eId, label: `IRN-${inv.id.slice(-3)}`, group: 'einvoice' });
                links.push({ source: invId, target: eId, label: 'E_INV', type: 'einvoice' });
            }
            // e-Way Bill node
            if (inv.eWayBill) {
                const wId = `w-${inv.id}`;
                nodes.push({ id: wId, label: `EWB-${inv.id.slice(-3)}`, group: 'ewaybill' });
                links.push({ source: invId, target: wId, label: 'EWB', type: 'ewaybill' });
            }
        });

        return { nodes, links };
    }, [vendors, invoices]);

    // Prefer the real graph from Neo4j; fall back to the client-side projection.
    const graphData = useMemo(
        () => (neo4jGraph ? { nodes: neo4jGraph.nodes, links: neo4jGraph.links } : localGraphData),
        [neo4jGraph, localGraphData]
    );
    const graphSource = neo4jGraph ? 'neo4j' : 'client';

    // ---- API Actions ----

    const addVendor = async (vendorData) => {
        const payload = {
            name: vendorData.name, gstin: vendorData.gstin, state: vendorData.state,
            totalTransactions: parseInt(vendorData.totalTransactions),
            missedFilings: parseInt(vendorData.missedFilings),
            avgDaysLate: parseInt(vendorData.avgDaysLate),
        };

        if (apiOnline) {
            try {
                const res = await fetch(`${API}/vendors`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const data = await res.json();
                // Refresh from DB
                await fetchAll();
                return data.vendor;
            } catch (err) { console.error('API error:', err); }
        }

        // Fallback: local
        const id = `V${String(vendors.length + 1).padStart(3, '0')}`;
        const riskScore = predictRisk(payload);
        const status = classifyRisk(riskScore);
        const newVendor = { id, ...payload, riskScore, status };
        setVendors(prev => [...prev, newVendor]);
        setAlerts(prev => [{ id: Date.now(), type: status === 'High Risk' ? 'critical' : 'success', message: `New vendor ${payload.name} added — Risk: ${(riskScore * 100).toFixed(0)}%`, time: 'Just now', icon: status === 'High Risk' ? '🔴' : '🟢' }, ...prev]);
        return newVendor;
    };

    const addInvoice = async (invoiceData) => {
        const payload = {
            vendorId: invoiceData.vendorId, date: invoiceData.date,
            taxableAmount: parseFloat(invoiceData.taxableAmount),
            cgst: parseFloat(invoiceData.cgst), sgst: parseFloat(invoiceData.sgst), igst: parseFloat(invoiceData.igst),
            hsn: invoiceData.hsn, period: invoiceData.period,
            gstr1Reported: invoiceData.gstr1Reported, gstr2bReported: invoiceData.gstr2bReported,
            eInvoice: invoiceData.eInvoice, eWayBill: invoiceData.eWayBill,
        };

        if (apiOnline) {
            try {
                const res = await fetch(`${API}/invoices`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                const data = await res.json();
                // Generate audit explanation client-side for mismatch
                if (data.invoice.matchStatus !== 'Matched') {
                    const vendor = vendors.find(v => v.id === payload.vendorId);
                    setAuditExplanations(prev => ({
                        ...prev,
                        [data.invoice.id]: {
                            summary: `Invoice ${data.invoice.id} (₹${payload.taxableAmount.toLocaleString('en-IN')} taxable) from ${vendor?.name || 'Unknown'} is flagged: ${data.invoice.matchStatus}.`,
                            evidence: [
                                `Invoice date: ${payload.date}, period: ${payload.period}`,
                                payload.gstr2bReported ? 'Invoice in GSTR-2B' : 'NOT in GSTR-2B',
                                payload.gstr1Reported ? 'Invoice in Vendor GSTR-1' : 'MISSING from Vendor GSTR-1',
                                payload.eInvoice ? 'e-Invoice generated' : 'No e-Invoice',
                                `Vendor risk: ${((vendor?.riskScore || 0) * 100).toFixed(0)}%`,
                            ],
                            recommendation: `ITC of ₹${data.invoice.totalTax.toLocaleString('en-IN')} is at risk. Contact vendor to reconcile.`,
                            graphPath: `Your Entity → GSTR-2B (${payload.period}) → ${data.invoice.id} → ${vendor?.name || 'Vendor'}`,
                        }
                    }));
                }
                await fetchAll();
                return data.invoice;
            } catch (err) { console.error('API error:', err); }
        }

        // Fallback: local
        const id = `INV-2025-${String(invoices.length + 1).padStart(3, '0')}`;
        const matchStatus = !payload.gstr1Reported && payload.gstr2bReported ? 'Missing in GSTR-1' : 'Matched';
        const totalTax = payload.cgst + payload.sgst + payload.igst;
        const vendor = vendors.find(v => v.id === payload.vendorId);
        const newInvoice = { id, ...payload, vendorName: vendor?.name || 'Unknown', gstin: vendor?.gstin || '', totalTax, total: payload.taxableAmount + totalTax, matchStatus, riskLevel: matchStatus !== 'Matched' ? 'High' : 'Low' };
        setInvoices(prev => [...prev, newInvoice]);
        return newInvoice;
    };

    // Scores a vendor with the trained RandomForest via the API, falling back to
    // the local heuristic when the backend is unreachable. `source` says which ran.
    const predictVendorRisk = async (features) => {
        if (apiOnline) {
            try {
                const res = await fetch(`${API}/predict-risk`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(features),
                });
                if (res.ok) {
                    const data = await res.json();
                    return {
                        score: data.score,
                        status: data.status,
                        source: data.source,
                        modelFeatures: data.features || null,
                        contributions: data.contributions || null,
                        features,
                    };
                }
            } catch (err) { console.warn('Prediction API unavailable, using heuristic:', err); }
        }

        const score = predictRisk(features);
        return { score, status: classifyRisk(score), source: 'heuristic', features };
    };

    // Rebuild the Neo4j projection from MongoDB.
    const syncGraph = async () => {
        try {
            const res = await fetch(`${API}/graph/sync`, { method: 'POST' });
            const data = await res.json();
            if (data.graph) setGraphStatus(data.graph);
            // Pull the rebuilt graph back so the visualisation reflects the sync.
            if (data.success) {
                try {
                    const g = await (await fetch(`${API}/graph/data`)).json();
                    setNeo4jGraph(g && g.available ? g : null);
                } catch { /* keep whatever we had */ }
            }
            return data;
        } catch {
            return { success: false, error: 'API unreachable' };
        }
    };

    // Run reconciliation server-side (Neo4j traversal, or the Mongo fallback).
    const runReconciliation = async (period) => {
        try {
            const qs = period && period !== 'all' ? `?period=${encodeURIComponent(period)}` : '';
            const res = await fetch(`${API}/reconcile${qs}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch {
            return { error: 'Could not reach the reconciliation API', engine: 'unavailable' };
        }
    };

    // Generate an audit trail for any flagged invoice from live graph facts.
    // Replaces the old hand-written lookup that only covered a few invoices.
    const fetchAuditTrail = async (invoiceId) => {
        try {
            const res = await fetch(`${API}/audit-trail/${encodeURIComponent(invoiceId)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch {
            return { error: 'The audit trail API is unreachable — start the backend to generate explanations.' };
        }
    };

    const fetchEvidence = async (invoiceId) => {
        try {
            const res = await fetch(`${API}/reconcile/evidence/${encodeURIComponent(invoiceId)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch { return null; }
    };

    const value = {
        vendors, invoices, mismatches, mismatchTypes, kpiData,
        graphData, alerts, auditExplanations, monthlyITCRisk,
        gstrReturns, riskFeatureImportance, complianceTrend,
        addVendor, addInvoice, predictVendorRisk, loading, apiOnline,
        modelInfo, graphStatus, graphSource, syncGraph, runReconciliation, fetchEvidence,
        fetchAuditTrail,
    };

    return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
}

export function useData() {
    const ctx = useContext(DataContext);
    if (!ctx) throw new Error('useData must be used within DataProvider');
    return ctx;
}
