import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import { motion } from 'framer-motion';
import { useData } from '../context/DataContext';
import { Eye, EyeOff, RotateCcw, ZoomIn, ZoomOut, Search, X, Database, AlertTriangle, Crosshair, ExternalLink, Network } from 'lucide-react';

const nodeColors = {
    taxpayer: '#f43f5e',
    vendor: '#f59e0b',
    invoice: '#3b82f6',
    gstr: '#22c55e',
    gstr3b: '#14b8a6',
    einvoice: '#a855f7',
    ewaybill: '#06b6d4',
};

const nodeLabels = {
    taxpayer: 'Taxpayer',
    vendor: 'Vendor',
    invoice: 'Invoice',
    gstr: 'GSTR-1 / 2B',
    gstr3b: 'GSTR-3B',
    einvoice: 'e-Invoice',
    ewaybill: 'e-Way Bill',
};

const edgeColors = {
    issued: 'rgba(245,158,11,0.55)',
    reported: 'rgba(34,197,94,0.5)',
    einvoice: 'rgba(168,85,247,0.42)',
    ewaybill: 'rgba(6,182,212,0.42)',
    billed: 'rgba(244,63,94,0.35)',
    purchase: 'rgba(244,63,94,0.55)',
    filed: 'rgba(20,184,166,0.5)',
    supplies: 'rgba(168,85,247,0.7)',
};

const DIM = 'rgba(100,116,139,0.12)';

// Node radius by type. Vendors read as the anchors of the graph, so they win.
const sizeFor = (group) =>
    group === 'taxpayer' ? 13 : group === 'vendor' ? 10
    : group === 'gstr' || group === 'gstr3b' ? 8.5
    : group === 'invoice' ? 6.5 : 4.5;

const nodeId = (end) => (typeof end === 'object' ? end.id : end);

export default function KnowledgeGraph() {
    const navigate = useNavigate();
    const { graphData, graphSource, graphStatus, vendors, invoices } = useData();
    const [selectedNode, setSelectedNode] = useState(null);
    const [hoverNode, setHoverNode] = useState(null);
    const [search, setSearch] = useState('');
    // Default to hiding unlinked nodes: with no edge holding them in, the charge
    // force pushes them to the far edge of the canvas and zoomToFit then has to
    // shrink the whole graph to include them. The toggle brings them back.
    const [hideOrphans, setHideOrphans] = useState(true);
    const [dimensions, setDimensions] = useState({ width: 800, height: 680 });
    const containerRef = useRef(null);
    const graphRef = useRef();
    const hasFramed = useRef(false);

    const [layers, setLayers] = useState({
        taxpayer: true, vendor: true, invoice: true, gstr: true,
        gstr3b: false,
        einvoice: true, ewaybill: true,
    });
    const toggleLayer = (key) => setLayers(prev => ({ ...prev, [key]: !prev[key] }));

    // ---- Filtering: layers, then optionally isolated nodes ----
    const filteredGraph = useMemo(() => {
        const visibleNodes = graphData.nodes.filter(n => layers[n.group]);
        const visibleIds = new Set(visibleNodes.map(n => n.id));
        const visibleLinks = graphData.links.filter(
            l => visibleIds.has(nodeId(l.source)) && visibleIds.has(nodeId(l.target))
        );

        if (!hideOrphans) return { nodes: visibleNodes, links: visibleLinks };

        // An orphan here is a node with no edge *within the current view* — e.g. a
        // vendor who has issued no invoices yet.
        const connected = new Set();
        visibleLinks.forEach(l => { connected.add(nodeId(l.source)); connected.add(nodeId(l.target)); });
        return { nodes: visibleNodes.filter(n => connected.has(n.id)), links: visibleLinks };
    }, [graphData, layers, hideOrphans]);

    const orphanCount = useMemo(() => {
        const connected = new Set();
        graphData.links.forEach(l => { connected.add(nodeId(l.source)); connected.add(nodeId(l.target)); });
        return graphData.nodes.filter(n => !connected.has(n.id)).length;
    }, [graphData]);

    // ---- Adjacency, for neighbour highlighting ----
    const adjacency = useMemo(() => {
        const map = new Map();
        filteredGraph.links.forEach(l => {
            const s = nodeId(l.source), t = nodeId(l.target);
            if (!map.has(s)) map.set(s, new Set());
            if (!map.has(t)) map.set(t, new Set());
            map.get(s).add(t);
            map.get(t).add(s);
        });
        return map;
    }, [filteredGraph]);

    // The node driving the highlight: hover takes priority over selection.
    const focusNode = hoverNode || selectedNode;
    const highlightIds = useMemo(() => {
        if (!focusNode) return null;
        const set = new Set([focusNode.id]);
        (adjacency.get(focusNode.id) || new Set()).forEach(id => set.add(id));
        return set;
    }, [focusNode, adjacency]);

    // ---- Search ----
    const searchMatches = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q) return null;
        return new Set(
            filteredGraph.nodes
                .filter(n =>
                    (n.fullName || n.label || '').toLowerCase().includes(q) ||
                    (n.vendorId || '').toLowerCase().includes(q) ||
                    (n.gstin || '').toLowerCase().includes(q) ||
                    (n.invoiceId || '').toLowerCase().includes(q) ||
                    (n.matchStatus || '').toLowerCase().includes(q) ||
                    (n.riskBand || '').toLowerCase().includes(q) ||
                    (n.state || '').toLowerCase().includes(q)
                )
                .map(n => n.id)
        );
    }, [search, filteredGraph]);

    const focusFirstMatch = useCallback(() => {
        if (!searchMatches?.size) return;
        const target = filteredGraph.nodes.find(n => searchMatches.has(n.id));
        if (target && graphRef.current) {
            graphRef.current.centerAt(target.x, target.y, 600);
            graphRef.current.zoom(3, 600);
            setSelectedNode(target);
        }
    }, [searchMatches, filteredGraph]);

    const stats = useMemo(() => ({
        vendors: graphData.nodes.filter(n => n.group === 'vendor').length || vendors.length,
        invoices: graphData.nodes.filter(n => n.group === 'invoice').length || invoices.length,
        flagged: graphData.nodes.filter(n => n.status === 'flagged').length,
        nodes: filteredGraph.nodes.length,
        edges: filteredGraph.links.length,
    }), [graphData, filteredGraph, vendors, invoices]);

    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                const rect = containerRef.current.getBoundingClientRect();
                setDimensions({ width: rect.width, height: 680 });
            }
        };
        updateDimensions();
        window.addEventListener('resize', updateDimensions);
        return () => window.removeEventListener('resize', updateDimensions);
    }, []);

    // Spread the layout out — the default charge packs 80+ nodes into an
    // unreadable knot. Tuned once per graph change; the actual framing happens
    // in onEngineStop below, when the simulation has settled.
    useEffect(() => {
        const g = graphRef.current;
        if (!g) return;
        g.d3Force('charge')?.strength(-520).distanceMax(700);
        g.d3Force('link')?.distance(l =>
            l.type === 'issued' ? 75 : l.type === 'filed' ? 26 : l.type === 'billed' ? 110 : 45
        ).strength(0.55);
        // Pull the whole drawing toward the canvas centre so it fills the frame
        // instead of drifting into one corner.
        g.d3Force('center')?.strength(0.06);
        g.d3ReheatSimulation?.();
    }, [filteredGraph]);

    // Frame the graph once the force simulation actually stops. Fitting on a
    // timer catches the layout mid-flight and leaves it small and off-centre.
    const handleEngineStop = useCallback(() => {
        if (!hasFramed.current) {
            graphRef.current?.zoomToFit(500, 55);
            hasFramed.current = true;
        }
    }, []);

    // Re-frame when the visible set changes (layer toggles, orphan filter).
    useEffect(() => { hasFramed.current = false; }, [filteredGraph]);

    const handleNodeClick = useCallback((node) => {
        setSelectedNode(node);
        if (graphRef.current) {
            graphRef.current.centerAt(node.x, node.y, 600);
            graphRef.current.zoom(2.8, 600);
        }
    }, []);

    // ---- Canvas painters ----
    const paintNode = useCallback((node, ctx, globalScale) => {
        const { group } = node;
        const isVendor = group === 'vendor' || group === 'taxpayer';
        const isInvoice = group === 'invoice';
        const isGstr = group === 'gstr' || group === 'gstr3b';
        const isDoc = group === 'einvoice' || group === 'ewaybill';
        const size = sizeFor(group);

        const dimmed = highlightIds ? !highlightIds.has(node.id) : false;
        const isMatch = searchMatches?.has(node.id);
        const isFocus = focusNode?.id === node.id;
        const color = dimmed ? DIM : (nodeColors[group] || '#fff');

        ctx.globalAlpha = dimmed ? 0.35 : 1;

        // Search hit: pulsing outer ring so it's findable in a dense graph.
        if (isMatch) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, size + 5, 0, 2 * Math.PI);
            ctx.strokeStyle = '#facc15';
            ctx.lineWidth = 1.6;
            ctx.stroke();
        }

        if (!dimmed && (isVendor || isFocus || (isInvoice && node.status === 'flagged'))) {
            ctx.shadowColor = isInvoice && node.status === 'flagged' ? '#ef4444' : nodeColors[group];
            ctx.shadowBlur = isFocus ? 20 : isVendor ? 14 : 10;
        }

        ctx.beginPath();
        if (isVendor) {
            for (let i = 0; i < 6; i++) {
                const angle = (Math.PI / 3) * i - Math.PI / 6;
                const x = node.x + size * Math.cos(angle);
                const y = node.y + size * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.closePath();
        } else if (isGstr) {
            ctx.moveTo(node.x, node.y - size);
            ctx.lineTo(node.x + size, node.y);
            ctx.lineTo(node.x, node.y + size);
            ctx.lineTo(node.x - size, node.y);
            ctx.closePath();
        } else if (isDoc) {
            ctx.rect(node.x - size / 2, node.y - size / 2, size, size);
        } else {
            ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
        }

        ctx.fillStyle = color;
        ctx.fill();
        ctx.shadowBlur = 0;

        if (!dimmed) {
            if (node.status === 'flagged') {
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
            if (isVendor && (node.risk > 0.6 || node.riskBand === 'HIGH')) {
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2.5;
                ctx.stroke();
            }
            if (isFocus) {
                ctx.strokeStyle = '#f8fafc';
                ctx.lineWidth = 1.5;
                ctx.stroke();
            }
        }

        // Labels scale with zoom so they stay legible instead of vanishing.
        // Minor nodes only get a label once you've zoomed in or focused them.
        const fontSize = Math.max(3.2, 11 / globalScale);
        const important =
            isVendor || group === 'gstr' || node.status === 'flagged';
        const showLabel = !dimmed && (important || isFocus || isMatch || globalScale > 2.2);

        if (showLabel) {
            ctx.font = `${isVendor ? '700 ' : '500 '}${fontSize}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            const text = (isVendor && node.vendorId) ? `${node.vendorId} · ${node.label}` : (node.label || '');
            const y = node.y + size + 2;

            // Backing plate keeps text readable over edges.
            if (isFocus || isMatch || globalScale > 2.2) {
                const w = ctx.measureText(text).width;
                ctx.fillStyle = 'rgba(15,23,42,0.78)';
                ctx.fillRect(node.x - w / 2 - 1.5, y - 0.5, w + 3, fontSize + 1.5);
            }
            ctx.fillStyle = isMatch ? '#facc15' : isVendor ? '#f1f5f9' : '#cbd5e1';
            ctx.fillText(text, node.x, y);
        }

        ctx.globalAlpha = 1;
    }, [highlightIds, searchMatches, focusNode]);

    const paintLink = useCallback((link, ctx) => {
        const s = nodeId(link.source), t = nodeId(link.target);
        const dimmed = highlightIds ? !(highlightIds.has(s) && highlightIds.has(t)) : false;
        const color = dimmed ? DIM : (edgeColors[link.type] || 'rgba(255,255,255,0.15)');

        ctx.globalAlpha = dimmed ? 0.25 : 1;
        ctx.strokeStyle = color;
        ctx.lineWidth = link.type === 'issued' ? 1.8 : 1;

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();

        if (!dimmed) {
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
        }
        ctx.globalAlpha = 1;
    }, [highlightIds]);

    // Neighbours of the selected node, for the detail panel.
    const neighbours = useMemo(() => {
        if (!selectedNode) return [];
        const ids = adjacency.get(selectedNode.id) || new Set();
        return filteredGraph.nodes.filter(n => ids.has(n.id));
    }, [selectedNode, adjacency, filteredGraph]);

    const fromNeo4j = graphSource === 'neo4j';

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <div className="page-header-row">
                    <div>
                        <h2>Knowledge Graph Explorer</h2>
                        <p>Interactive entity graph of GST vendors, invoices, returns, and compliance documents</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span className={`badge ${fromNeo4j ? 'compliant' : 'review'}`} title={
                            fromNeo4j
                                ? `Read from Neo4j at ${graphStatus?.uri || 'bolt://localhost:7687'}`
                                : `Neo4j unavailable (${graphStatus?.reason || 'not connected'}) — projection built in the browser from MongoDB rows`
                        }>
                            <Database size={11} style={{ marginRight: 4, verticalAlign: -1 }} />
                            {fromNeo4j ? 'Live from Neo4j' : 'Client-side projection'}
                        </span>
                        <span className="badge info">{stats.nodes} nodes · {stats.edges} edges</span>
                        <button
                            className="btn btn-outline btn-sm"
                            style={{ padding: '3px 10px', fontSize: '0.72rem', gap: '4px' }}
                            onClick={() => navigate('/graph-explorer')}
                            title="Open Temporal Counterparty Trading Topology view"
                        >
                            <Network size={12} /> Trading Topology View
                        </button>
                    </div>
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

            {/* Search + Layer Toggles + Controls */}
            <div className="card mb-2" style={{ padding: '12px 20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div style={{ position: 'relative', minWidth: '260px' }}>
                        <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="filter-input"
                            style={{ paddingLeft: '32px', paddingRight: search ? '30px' : '10px', width: '100%', fontSize: '0.8rem' }}
                            placeholder="Search vendor, GSTIN, invoice, status…"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && focusFirstMatch()}
                        />
                        {search && (
                            <button
                                onClick={() => setSearch('')}
                                style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}
                                title="Clear search"
                            >
                                <X size={13} />
                            </button>
                        )}
                    </div>

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
                        {orphanCount > 0 && (
                            <button
                                className={`btn ${hideOrphans ? 'btn-primary' : 'btn-secondary'}`}
                                style={{ padding: '4px 10px', fontSize: '0.72rem', gap: '4px' }}
                                onClick={() => setHideOrphans(v => !v)}
                                title={`${orphanCount} node(s) have no relationships in the graph — typically vendors who have not issued an invoice yet`}
                            >
                                <Crosshair size={12} /> {hideOrphans ? `Show ${orphanCount} unlinked` : `Hide ${orphanCount} unlinked`}
                            </button>
                        )}
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} title="Zoom in" onClick={() => graphRef.current?.zoom(graphRef.current.zoom() * 1.5, 300)}><ZoomIn size={14} /></button>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} title="Zoom out" onClick={() => graphRef.current?.zoom(graphRef.current.zoom() * 0.7, 300)}><ZoomOut size={14} /></button>
                        <button className="btn btn-secondary" style={{ padding: '4px 8px' }} title="Reset view" onClick={() => { graphRef.current?.zoomToFit(400, 60); setSelectedNode(null); setSearch(''); }}><RotateCcw size={14} /></button>
                    </div>
                </div>

                {search && (
                    <div style={{ marginTop: '8px', fontSize: '0.75rem', color: searchMatches?.size ? 'var(--text-secondary)' : 'var(--danger)' }}>
                        {searchMatches?.size
                            ? <>{searchMatches.size} match{searchMatches.size === 1 ? '' : 'es'} ringed in yellow — press Enter to jump to the first</>
                            : 'No nodes match that search'}
                    </div>
                )}
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
                    nodePointerAreaPaint={(node, color, ctx) => {
                        // Generous hit area so small document nodes stay clickable.
                        ctx.fillStyle = color;
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, sizeFor(node.group) + 3, 0, 2 * Math.PI);
                        ctx.fill();
                    }}
                    linkCanvasObject={paintLink}
                    onNodeClick={handleNodeClick}
                    onNodeHover={setHoverNode}
                    onBackgroundClick={() => setSelectedNode(null)}
                    nodeRelSize={6}
                    linkDirectionalParticles={focusNode ? 0 : 1}
                    linkDirectionalParticleSpeed={0.004}
                    linkDirectionalParticleWidth={1.5}
                    linkDirectionalParticleColor={(link) => edgeColors[link.type] || '#fff'}
                    d3AlphaDecay={0.022}
                    d3VelocityDecay={0.32}
                    cooldownTicks={320}
                    onEngineStop={handleEngineStop}
                    enableZoomInteraction
                    enablePanInteraction
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
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '8px', borderTop: '1px solid var(--border-primary)', paddingTop: '6px', lineHeight: 1.6 }}>
                        <div><span style={{ color: '#ef4444' }}>●</span> Red ring = flagged / high risk</div>
                        <div><span style={{ color: '#facc15' }}>●</span> Yellow ring = search match</div>
                        <div>Hover to isolate · click to inspect</div>
                        <div style={{ marginTop: '4px' }}>Enable <strong>GSTR-3B</strong> to see the tax-payment layer</div>
                    </div>
                </div>

                {/* Hover hint */}
                {hoverNode && !selectedNode && (
                    <div style={{
                        position: 'absolute', top: '12px', left: '12px', padding: '6px 12px',
                        background: 'rgba(15,23,42,0.9)', border: '1px solid var(--border-primary)',
                        borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-secondary)', pointerEvents: 'none',
                    }}>
                        <strong style={{ color: nodeColors[hoverNode.group] }}>{hoverNode.fullName || hoverNode.label}</strong>
                        {' · '}{nodeLabels[hoverNode.group]}
                        {typeof hoverNode.degree === 'number' && <> · {hoverNode.degree} link{hoverNode.degree === 1 ? '' : 's'}</>}
                    </div>
                )}

            {/* Node Detail Panel — overlaid on the canvas so it is visible the
                moment a node is clicked, rather than below a 680px graph. */}
            {selectedNode && (
                <motion.div
                    className="node-detail-panel"
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    style={{
                        position: 'absolute', top: '12px', right: '12px', width: '310px',
                        maxHeight: 'calc(100% - 24px)', overflowY: 'auto', marginTop: 0,
                        background: 'rgba(15,23,42,0.96)', backdropFilter: 'blur(6px)', zIndex: 5,
                    }}
                >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <h4>{selectedNode.fullName || selectedNode.label}</h4>
                        <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} title="Close"><X size={15} /></button>
                    </div>

                    <div className="node-detail-row">
                        <span className="node-detail-label">Type</span>
                        <span className="node-detail-value">
                            <span className="badge" style={{ background: nodeColors[selectedNode.group] + '22', color: nodeColors[selectedNode.group] }}>
                                {nodeLabels[selectedNode.group] || selectedNode.group}
                            </span>
                        </span>
                    </div>

                    {selectedNode.vendorId && <div className="node-detail-row">
                        <span className="node-detail-label">Vendor ID</span>
                        <span className="node-detail-value font-mono text-accent">{selectedNode.vendorId}</span>
                    </div>}
                    {selectedNode.invoiceId && <div className="node-detail-row">
                        <span className="node-detail-label">Invoice</span>
                        <span className="node-detail-value font-mono">{selectedNode.invoiceId}</span>
                    </div>}
                    {selectedNode.gstin && <div className="node-detail-row">
                        <span className="node-detail-label">GSTIN</span>
                        <span className="node-detail-value font-mono">{selectedNode.gstin}</span>
                    </div>}
                    {selectedNode.state && <div className="node-detail-row">
                        <span className="node-detail-label">State</span>
                        <span className="node-detail-value">{selectedNode.state}</span>
                    </div>}
                    {selectedNode.risk !== undefined && selectedNode.risk !== null && <div className="node-detail-row">
                        <span className="node-detail-label">Trained Risk Score</span>
                        <span className="node-detail-value">
                            <span className={`badge ${selectedNode.risk > 0.6 || selectedNode.riskBand === 'HIGH' ? 'high' : selectedNode.risk > 0.3 || selectedNode.riskBand === 'MEDIUM' ? 'medium' : 'low'}`}>
                                {(selectedNode.risk * 100).toFixed(1)}% {selectedNode.riskBand ? `(${selectedNode.riskBand})` : ''}
                            </span>
                        </span>
                    </div>}
                    {selectedNode.itcExposure !== undefined && selectedNode.itcExposure !== null && selectedNode.itcExposure > 0 && <div className="node-detail-row">
                        <span className="node-detail-label">ITC at Risk</span>
                        <span className="node-detail-value amount" style={{ color: '#ef4444', fontWeight: 600 }}>
                            ₹{Number(selectedNode.itcExposure).toLocaleString('en-IN')}
                        </span>
                    </div>}
                    {selectedNode.priority && <div className="node-detail-row">
                        <span className="node-detail-label">ML Priority</span>
                        <span className="node-detail-value font-semibold">{selectedNode.priority}</span>
                    </div>}
                    {selectedNode.mismatchRate !== undefined && selectedNode.mismatchRate !== null && <div className="node-detail-row">
                        <span className="node-detail-label">Mismatch Rate</span>
                        <span className="node-detail-value">{Number(selectedNode.mismatchRate).toFixed(1)}%</span>
                    </div>}
                    {selectedNode.centrality !== undefined && selectedNode.centrality !== null && <div className="node-detail-row">
                        <span className="node-detail-label">Graph Centrality</span>
                        <span className="node-detail-value font-mono">{Number(selectedNode.centrality).toFixed(2)}</span>
                    </div>}
                    {selectedNode.amount ? <div className="node-detail-row">
                        <span className="node-detail-label">Invoice Value</span>
                        <span className="node-detail-value amount">₹{selectedNode.amount.toLocaleString('en-IN')}</span>
                    </div> : null}
                    {selectedNode.totalTax ? <div className="node-detail-row">
                        <span className="node-detail-label">Tax</span>
                        <span className="node-detail-value amount">₹{selectedNode.totalTax.toLocaleString('en-IN')}</span>
                    </div> : null}
                    {selectedNode.hsn && <div className="node-detail-row">
                        <span className="node-detail-label">HSN</span>
                        <span className="node-detail-value font-mono">{selectedNode.hsn}</span>
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
                        <span className="node-detail-value">{neighbours.length}</span>
                    </div>

                    {/* The ITC-blocking case, stated plainly */}
                    {selectedNode.group === 'invoice' && selectedNode.status === 'flagged' && (
                        <div style={{ marginTop: '10px', padding: '8px 10px', borderRadius: '6px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', gap: '8px' }}>
                            <AlertTriangle size={14} style={{ color: 'var(--danger)', flexShrink: 0, marginTop: 1 }} />
                            <span>
                                {selectedNode.matchStatus === 'Missing in GSTR-1'
                                    ? <>No <span className="font-mono">:REPORTED_IN</span> edge to GSTR-1 — the supplier never filed it, so ITC is blocked under s.16(2)(aa).</>
                                    : <>Flagged: {selectedNode.matchStatus}.</>}
                            </span>
                        </div>
                    )}

                    {neighbours.length > 0 && (
                        <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-primary)', paddingTop: '8px' }}>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
                                Connected Entities
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                {neighbours.slice(0, 14).map(n => (
                                    <button
                                        key={n.id}
                                        onClick={() => handleNodeClick(n)}
                                        className="badge"
                                        style={{ background: nodeColors[n.group] + '1e', color: nodeColors[n.group], border: 'none', cursor: 'pointer', fontSize: '0.7rem' }}
                                        title={`Jump to ${n.fullName || n.label}`}
                                    >
                                        {n.label}
                                    </button>
                                ))}
                                {neighbours.length > 14 && (
                                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                                        +{neighbours.length - 14} more
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {selectedNode.group === 'vendor' && (
                        <div style={{ marginTop: '14px', borderTop: '1px solid var(--border-primary)', paddingTop: '10px' }}>
                            <button
                                onClick={() => navigate(`/investigation/${selectedNode.vendorId || selectedNode.id.replace('v-', '')}`)}
                                className="btn btn-primary btn-sm"
                                style={{ width: '100%', justifyContent: 'center', fontSize: '0.75rem', gap: '6px' }}
                            >
                                <ExternalLink size={13} /> Open Investigation Workspace
                            </button>
                        </div>
                    )}
                </motion.div>
            )}
            </div>
        </motion.div>
    );
}
