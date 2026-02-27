import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { motion } from 'framer-motion';
import { useData } from '../context/DataContext';
import { Eye, EyeOff, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';

const nodeColors = {
    vendor: '#f59e0b',
    invoice: '#3b82f6',
    gstr: '#22c55e',
    einvoice: '#a855f7',
    ewaybill: '#06b6d4',
};

const nodeLabels = {
    vendor: 'Vendor',
    invoice: 'Invoice',
    gstr: 'GSTR Return',
    einvoice: 'e-Invoice',
    ewaybill: 'e-Way Bill',
};

const edgeColors = {
    issued: 'rgba(245,158,11,0.5)',
    reported: 'rgba(34,197,94,0.45)',
    einvoice: 'rgba(168,85,247,0.4)',
    ewaybill: 'rgba(6,182,212,0.4)',
};

export default function KnowledgeGraph() {
    const { graphData, vendors, invoices } = useData();
    const [selectedNode, setSelectedNode] = useState(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 550 });
    const containerRef = useRef(null);
    const graphRef = useRef();

    // Layer visibility toggles
    const [layers, setLayers] = useState({
        vendor: true, invoice: true, gstr: true, einvoice: true, ewaybill: true,
    });

    const toggleLayer = (key) => setLayers(prev => ({ ...prev, [key]: !prev[key] }));

    // Filter graph data based on visible layers
    const filteredGraph = useMemo(() => {
        const visibleNodes = graphData.nodes.filter(n => layers[n.group]);
        const visibleIds = new Set(visibleNodes.map(n => n.id));
        const visibleLinks = graphData.links.filter(l => {
            const sId = typeof l.source === 'object' ? l.source.id : l.source;
            const tId = typeof l.target === 'object' ? l.target.id : l.target;
            return visibleIds.has(sId) && visibleIds.has(tId);
        });
        return { nodes: visibleNodes, links: visibleLinks };
    }, [graphData, layers]);

    // Stats
    const stats = useMemo(() => ({
        vendors: vendors.length,
        invoices: invoices.length,
        flagged: invoices.filter(i => i.matchStatus !== 'Matched').length,
        nodes: filteredGraph.nodes.length,
        edges: filteredGraph.links.length,
    }), [vendors, invoices, filteredGraph]);

    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                const rect = containerRef.current.getBoundingClientRect();
                setDimensions({ width: rect.width, height: 550 });
            }
        };
        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    const handleNodeClick = useCallback((node) => {
        setSelectedNode(node);
        if (graphRef.current) {
            graphRef.current.centerAt(node.x, node.y, 600);
            graphRef.current.zoom(2.5, 600);
        }
    }, []);

    const paintNode = useCallback((node, ctx) => {
        const isVendor = node.group === 'vendor';
        const isInvoice = node.group === 'invoice';
        const isGstr = node.group === 'gstr';
        const isDoc = node.group === 'einvoice' || node.group === 'ewaybill';
        const size = isVendor ? 10 : isGstr ? 8 : isInvoice ? 7 : 5;
        const color = nodeColors[node.group] || '#fff';

        // Glow for main entities
        if (isVendor || (isInvoice && node.status === 'flagged')) {
            ctx.shadowColor = isInvoice ? '#ef4444' : color;
            ctx.shadowBlur = isVendor ? 15 : 10;
        }

        ctx.beginPath();
        if (isVendor) {
            // Hexagon
            for (let i = 0; i < 6; i++) {
                const angle = (Math.PI / 3) * i - Math.PI / 6;
                const x = node.x + size * Math.cos(angle);
                const y = node.y + size * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.closePath();
        } else if (isGstr) {
            // Diamond
            ctx.moveTo(node.x, node.y - size);
            ctx.lineTo(node.x + size, node.y);
            ctx.lineTo(node.x, node.y + size);
            ctx.lineTo(node.x - size, node.y);
            ctx.closePath();
        } else if (isDoc) {
            // Small square
            ctx.rect(node.x - size / 2, node.y - size / 2, size, size);
        } else {
            // Circle for invoices
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
        }

        ctx.fillStyle = color;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Red ring for flagged invoices
        if (node.status === 'flagged') {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        // High risk vendor ring
        if (isVendor && node.risk > 0.6) {
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 2.5;
            ctx.stroke();
        }

        // Label (only for vendors, GSTR, flagged invoices)
        if (isVendor || isGstr || (isInvoice && node.status === 'flagged')) {
            ctx.font = `${isVendor ? 'bold ' : ''}3.5px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#cbd5e1';
            ctx.fillText(node.label, node.x, node.y + size + 2);
        }
    }, []);

    const paintLink = useCallback((link, ctx) => {
        const color = edgeColors[link.type] || 'rgba(255,255,255,0.15)';
        ctx.strokeStyle = color;
        ctx.lineWidth = link.type === 'issued' ? 1.8 : 1;

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();

        // Directional arrow at midpoint
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const angle = Math.atan2(dy, dx);
        const midX = (link.source.x + link.target.x) / 2;
        const midY = (link.source.y + link.target.y) / 2;
        const arrLen = 3;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(midX + arrLen * Math.cos(angle), midY + arrLen * Math.sin(angle));
        ctx.lineTo(midX + arrLen * Math.cos(angle - 2.5), midY + arrLen * Math.sin(angle - 2.5));
        ctx.lineTo(midX + arrLen * Math.cos(angle + 2.5), midY + arrLen * Math.sin(angle + 2.5));
        ctx.fill();
    }, []);

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <div className="page-header-row">
                    <div>
                        <h2>Knowledge Graph Explorer</h2>
                        <p>Interactive entity graph of GST vendors, invoices, returns, and compliance documents</p>
                    </div>
                    <span className="badge info">{stats.nodes} nodes · {stats.edges} edges</span>
                </div>
            </div>

            {/* Stats Bar */}
            <div className="kpi-grid mb-2" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
                <div className="kpi-card" style={{ borderColor: 'rgba(245,158,11,0.3)' }}>
                    <div className="kpi-label">Vendors</div>
                    <div className="kpi-value" style={{ color: '#f59e0b' }}>{stats.vendors}</div>
                </div>
                <div className="kpi-card" style={{ borderColor: 'rgba(59,130,246,0.3)' }}>
                    <div className="kpi-label">Invoices</div>
                    <div className="kpi-value" style={{ color: '#3b82f6' }}>{stats.invoices}</div>
                </div>
                <div className="kpi-card" style={{ borderColor: 'rgba(239,68,68,0.3)' }}>
                    <div className="kpi-label">Flagged</div>
                    <div className="kpi-value" style={{ color: '#ef4444' }}>{stats.flagged}</div>
                </div>
                <div className="kpi-card" style={{ borderColor: 'rgba(34,197,94,0.3)' }}>
                    <div className="kpi-label">GSTR Nodes</div>
                    <div className="kpi-value" style={{ color: '#22c55e' }}>{filteredGraph.nodes.filter(n => n.group === 'gstr').length}</div>
                </div>
                <div className="kpi-card" style={{ borderColor: 'rgba(168,85,247,0.3)' }}>
                    <div className="kpi-label">Documents</div>
                    <div className="kpi-value" style={{ color: '#a855f7' }}>{filteredGraph.nodes.filter(n => n.group === 'einvoice' || n.group === 'ewaybill').length}</div>
                </div>
            </div>

            {/* Layer Toggles + Controls */}
            <div className="card mb-2" style={{ padding: '12px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {Object.entries(nodeLabels).map(([key, label]) => (
                            <button
                                key={key}
                                className={`btn ${layers[key] ? 'btn-primary' : 'btn-secondary'}`}
                                style={{ padding: '4px 12px', fontSize: '0.75rem', gap: '5px', opacity: layers[key] ? 1 : 0.5 }}
                                onClick={() => toggleLayer(key)}
                            >
                                <div style={{ width: 8, height: 8, borderRadius: '50%', background: nodeColors[key] }}></div>
                                {layers[key] ? <Eye size={12} /> : <EyeOff size={12} />}
                                {label}
                            </button>
                        ))}
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} onClick={() => { if (graphRef.current) graphRef.current.zoom(graphRef.current.zoom() * 1.5, 300); }}><ZoomIn size={14} /></button>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} onClick={() => { if (graphRef.current) graphRef.current.zoom(graphRef.current.zoom() * 0.7, 300); }}><ZoomOut size={14} /></button>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} onClick={() => { if (graphRef.current) graphRef.current.zoomToFit(400, 40); setSelectedNode(null); }}><RotateCcw size={14} /></button>
                    </div>
                </div>
            </div>

            {/* Graph Canvas */}
            <div className="graph-container" ref={containerRef} style={{ position: 'relative' }}>
                <ForceGraph2D
                    ref={graphRef}
                    graphData={filteredGraph}
                    width={dimensions.width}
                    height={dimensions.height}
                    backgroundColor="#0f172a"
                    nodeCanvasObject={paintNode}
                    linkCanvasObject={paintLink}
                    onNodeClick={handleNodeClick}
                    onBackgroundClick={() => setSelectedNode(null)}
                    nodeRelSize={6}
                    linkDirectionalParticles={1}
                    linkDirectionalParticleSpeed={0.004}
                    linkDirectionalParticleWidth={1.5}
                    linkDirectionalParticleColor={(link) => edgeColors[link.type] || '#fff'}
                    d3AlphaDecay={0.03}
                    d3VelocityDecay={0.35}
                    cooldownTicks={150}
                    d3Force="charge"
                    d3ForceStrength={-80}
                    enableZoomInteraction={true}
                    enablePanInteraction={true}
                />
                {/* Legend overlay */}
                <div className="graph-legend">
                    <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Entity Types</div>
                    {Object.entries(nodeLabels).map(([key, label]) => (
                        <div key={key} className="legend-item" style={{ opacity: layers[key] ? 1 : 0.3 }}>
                            <div className="legend-dot" style={{ background: nodeColors[key] }}></div>
                            <span>{label}</span>
                        </div>
                    ))}
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '8px', borderTop: '1px solid var(--border-primary)', paddingTop: '6px' }}>
                        <div style={{ marginBottom: '2px' }}><span style={{ color: '#ef4444' }}>●</span> Red ring = flagged/high risk</div>
                        <div>Click nodes for details</div>
                    </div>
                </div>
            </div>

            {/* Node Detail Panel */}
            {selectedNode && (
                <motion.div
                    className="node-detail-panel"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h4>Node: {selectedNode.label}</h4>
                    <div className="node-detail-row">
                        <span className="node-detail-label">Type</span>
                        <span className="node-detail-value">
                            <span className="badge" style={{ background: nodeColors[selectedNode.group] + '22', color: nodeColors[selectedNode.group] }}>
                                {nodeLabels[selectedNode.group] || selectedNode.group}
                            </span>
                        </span>
                    </div>
                    <div className="node-detail-row">
                        <span className="node-detail-label">ID</span>
                        <span className="node-detail-value font-mono">{selectedNode.id}</span>
                    </div>
                    {selectedNode.gstin && <div className="node-detail-row">
                        <span className="node-detail-label">GSTIN</span>
                        <span className="node-detail-value font-mono">{selectedNode.gstin}</span>
                    </div>}
                    {selectedNode.state && <div className="node-detail-row">
                        <span className="node-detail-label">State</span>
                        <span className="node-detail-value">{selectedNode.state}</span>
                    </div>}
                    {selectedNode.risk !== undefined && <div className="node-detail-row">
                        <span className="node-detail-label">Risk Score</span>
                        <span className="node-detail-value">
                            <span className={`badge ${selectedNode.risk > 0.6 ? 'high' : selectedNode.risk > 0.3 ? 'medium' : 'low'}`}>
                                {(selectedNode.risk * 100).toFixed(0)}%
                            </span>
                        </span>
                    </div>}
                    {selectedNode.amount && <div className="node-detail-row">
                        <span className="node-detail-label">Amount</span>
                        <span className="node-detail-value amount">₹{selectedNode.amount.toLocaleString('en-IN')}</span>
                    </div>}
                    {selectedNode.matchStatus && <div className="node-detail-row">
                        <span className="node-detail-label">Match Status</span>
                        <span className="node-detail-value" style={{ color: selectedNode.matchStatus === 'Matched' ? 'var(--success)' : 'var(--danger)' }}>
                            {selectedNode.matchStatus}
                        </span>
                    </div>}
                    {selectedNode.type && <div className="node-detail-row">
                        <span className="node-detail-label">Return Type</span>
                        <span className="node-detail-value">{selectedNode.type}</span>
                    </div>}
                    {selectedNode.period && <div className="node-detail-row">
                        <span className="node-detail-label">Period</span>
                        <span className="node-detail-value">{selectedNode.period}</span>
                    </div>}
                    <div className="node-detail-row">
                        <span className="node-detail-label">Connections</span>
                        <span className="node-detail-value">{filteredGraph.links.filter(l => {
                            const sId = typeof l.source === 'object' ? l.source.id : l.source;
                            const tId = typeof l.target === 'object' ? l.target.id : l.target;
                            return sId === selectedNode.id || tId === selectedNode.id;
                        }).length}</span>
                    </div>
                </motion.div>
            )}
        </motion.div>
    );
}
