import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Network,
  Calendar,
  Layers,
  Search,
  AlertCircle,
  RefreshCw,
  Info,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Target,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ArrowUpRight,
  ArrowDownLeft,
  Repeat,
  Sliders,
  Filter
} from 'lucide-react';
import { getVendorGraph } from '../api/riskApi';
import ResearchDisclaimer from '../components/ResearchDisclaimer';

const AVAILABLE_PERIODS = [
  '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09',
  '2024-10', '2024-11', '2024-12', '2025-01', '2025-02', '2025-03',
  '2025-04', '2025-05', '2025-06', '2025-07', '2025-08', '2025-09',
  '2025-10', '2025-11', '2025-12', '2026-01', '2026-02'
];

function formatINR(val) {
  if (val === undefined || val === null) return '₹0';
  const num = Number(val);
  if (isNaN(num)) return '₹0';
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `₹${(num / 100000).toFixed(1)} L`;
  if (num >= 1000) return `₹${(num / 1000).toFixed(1)} K`;
  return `₹${num.toFixed(0)}`;
}

export default function KnowledgeGraphExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const initialVendor = searchParams.get('vendor') || 'V0001';
  const initialPeriod = searchParams.get('period') || '2026-02';
  const initialDepth = parseInt(searchParams.get('depth') || '1', 10);

  const [vendorId, setVendorId] = useState(initialVendor);
  const [vendorInput, setVendorInput] = useState(initialVendor);
  const [period, setPeriod] = useState(initialPeriod);
  const [depth, setDepth] = useState(initialDepth === 2 ? 2 : 1);

  // Layout mode: 'concentric' (focal vendor in center, suppliers left, customers right) or 'force'
  const [layoutMode, setLayoutMode] = useState('concentric');
  // Filter type: 'ALL', 'SUPPLIERS', 'CUSTOMERS', 'RECIPROCAL', 'HIGH_RISK'
  const [filterType, setFilterType] = useState('ALL');

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selection & Hover States
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoverNode, setHoverNode] = useState(null);
  const [hoverLink, setHoverLink] = useState(null);

  // Collapsible Guide state
  const [guideOpen, setGuideOpen] = useState(false);

  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Update URL params
  useEffect(() => {
    setSearchParams({ vendor: vendorId, period, depth: depth.toString() }, { replace: true });
  }, [vendorId, period, depth]);

  // Handle Resize
  useEffect(() => {
    function updateDimensions() {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 800,
          height: 600,
        });
      }
    }
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const loadGraph = async () => {
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setHoverNode(null);
    setHoverLink(null);
    try {
      const data = await getVendorGraph(vendorId, period, depth);
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load graph:', err);
      setError(err.message || 'Unable to retrieve Knowledge Graph neighborhood.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [vendorId, period, depth]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (vendorInput.trim()) {
      setVendorId(vendorInput.trim().toUpperCase());
    }
  };

  // Switch center vendor directly
  const handleRecenter = (newVendorId) => {
    if (!newVendorId) return;
    setVendorId(newVendorId);
    setVendorInput(newVendorId);
    setSelectedNode(null);
  };

  // Node filtering logic
  const filteredNodes = useMemo(() => {
    if (!graphData?.nodes) return [];
    if (filterType === 'ALL') return graphData.nodes;
    return graphData.nodes.filter(n => {
      if (n.is_target) return true; // always show focal vendor
      if (filterType === 'SUPPLIERS') return n.node_type === 'supplier' || n.node_type === 'reciprocal';
      if (filterType === 'CUSTOMERS') return n.node_type === 'customer' || n.node_type === 'reciprocal';
      if (filterType === 'RECIPROCAL') return n.node_type === 'reciprocal';
      if (filterType === 'HIGH_RISK') return n.risk_band === 'HIGH' || n.risk_score >= 70;
      return true;
    });
  }, [graphData, filterType]);

  const filteredEdges = useMemo(() => {
    if (!graphData?.edges) return [];
    const validIds = new Set(filteredNodes.map(n => n.id));
    return graphData.edges.filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source;
      const t = typeof e.target === 'object' ? e.target.id : e.target;
      return validIds.has(s) && validIds.has(t);
    });
  }, [graphData, filteredNodes]);

  // Coordinate computation for structured concentric layout vs force-directed
  const processedGraphData = useMemo(() => {
    if (!filteredNodes.length) return { nodes: [], links: [] };

    // Deep copy to prevent React state mutation conflicts
    const nodes = filteredNodes.map(n => ({ ...n }));
    const links = filteredEdges.map(e => ({ ...e }));

    if (layoutMode === 'concentric') {
      const target = nodes.find(n => n.is_target);
      const suppliers = nodes.filter(n => !n.is_target && n.node_type === 'supplier');
      const customers = nodes.filter(n => !n.is_target && n.node_type === 'customer');
      const reciprocals = nodes.filter(n => !n.is_target && n.node_type === 'reciprocal');
      const peers = nodes.filter(n => !n.is_target && (n.node_type === 'peer' || !['supplier', 'customer', 'reciprocal'].includes(n.node_type)));

      // 1. Center Focal Entity at origin (0, 0)
      if (target) {
        target.fx = 0;
        target.fy = 0;
        target.x = 0;
        target.y = 0;
      }

      // 2. Direct Suppliers on left arc (120 deg to 240 deg)
      const R1 = 180;
      suppliers.forEach((s, idx) => {
        const step = suppliers.length > 1 ? 120 / (suppliers.length - 1) : 0;
        const angle = (120 + idx * step) * (Math.PI / 180);
        s.fx = R1 * Math.cos(angle);
        s.fy = R1 * Math.sin(angle);
        s.x = s.fx;
        s.y = s.fy;
      });

      // 3. Direct Customers on right arc (-60 deg to +60 deg)
      customers.forEach((c, idx) => {
        const step = customers.length > 1 ? 120 / (customers.length - 1) : 0;
        const angle = (-60 + idx * step) * (Math.PI / 180);
        c.fx = R1 * Math.cos(angle);
        c.fy = R1 * Math.sin(angle);
        c.x = c.fx;
        c.y = c.fy;
      });

      // 4. Reciprocal Partners at top and bottom poles
      reciprocals.forEach((r, idx) => {
        const angle = (idx % 2 === 0 ? -90 : 90) * (Math.PI / 180);
        const radius = R1 + Math.floor(idx / 2) * 40;
        r.fx = radius * Math.cos(angle);
        r.fy = radius * Math.sin(angle);
        r.x = r.fx;
        r.y = r.fy;
      });

      // 5. Tier-2 / Multi-Hop Peers on outer perimeter
      const R2 = 320;
      peers.forEach((p, idx) => {
        const angle = (idx * (360 / Math.max(peers.length, 1))) * (Math.PI / 180);
        p.fx = R2 * Math.cos(angle);
        p.fy = R2 * Math.sin(angle);
        p.x = p.fx;
        p.y = p.fy;
      });
    } else {
      // Force-directed mode: let physics simulate, lightly pin target node
      nodes.forEach(n => {
        if (n.is_target) {
          n.fx = 0;
          n.fy = 0;
        } else {
          n.fx = undefined;
          n.fy = undefined;
        }
      });
    }

    return { nodes, links };
  }, [filteredNodes, filteredEdges, layoutMode]);

  // Zoom and Canvas Controls
  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.35, 300);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.35, 300);
    }
  };

  const handleFit = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 35);
    }
  };

  const handleCenterFocal = () => {
    if (graphRef.current) {
      graphRef.current.centerAt(0, 0, 400);
      graphRef.current.zoom(1.2, 400);
    }
  };

  // Custom Node Canvas Painting: Dual-Ring + Icons + Crisp Labels
  const drawNode = useCallback((node, ctx, globalScale) => {
    const isSelected = selectedNode && selectedNode.id === node.id;
    const isHovered = hoverNode && hoverNode.id === node.id;
    const isTarget = node.is_target;

    // Node radius
    const r = isTarget ? 14 : (node.node_type === 'reciprocal' ? 10.5 : 8.5);

    // 1. Ambient / Selection Glow
    if (isSelected || isHovered || isTarget) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + (isSelected ? 8 : (isTarget ? 6 : 4)), 0, 2 * Math.PI);
      ctx.fillStyle = isSelected
        ? 'rgba(59, 130, 246, 0.45)'
        : (isTarget ? 'rgba(245, 158, 11, 0.35)' : 'rgba(255, 255, 255, 0.18)');
      ctx.fill();
      if (isSelected) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#60a5fa';
        ctx.stroke();
      }
    }

    // 2. Outer Ring: Risk Band encoding
    // Red = High Risk, Amber = Medium Risk, Green = Low Risk
    const isHighRisk = node.risk_band === 'HIGH' || node.risk_score >= 70;
    const isMedRisk = node.risk_band === 'MEDIUM' || (node.risk_score >= 35 && node.risk_score < 70);
    const riskRingColor = isHighRisk ? '#ef4444' : (isMedRisk ? '#f59e0b' : '#10b981');

    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = riskRingColor;

    // 3. Inner Core Fill: Role Color
    let roleColor = '#64748b'; // default peer (slate)
    if (isTarget) roleColor = '#f59e0b'; // Gold for Focal Entity
    else if (node.node_type === 'reciprocal') roleColor = '#8b5cf6'; // Violet for bilateral/reciprocal
    else if (node.node_type === 'supplier') roleColor = '#06b6d4'; // Cyan for inward supplier
    else if (node.node_type === 'customer') roleColor = '#3b82f6'; // Blue for outward customer

    ctx.fillStyle = roleColor;
    ctx.fill();
    ctx.stroke();

    // 4. Center Monogram / Symbol
    const symbol = isTarget ? '★' : (node.node_type === 'reciprocal' ? '⇄' : (node.node_type === 'supplier' ? 'IN' : (node.node_type === 'customer' ? 'OUT' : '●')));
    ctx.font = `bold ${Math.max(6, Math.min(10, r * 0.9))}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(symbol, node.x, node.y);

    // 5. Readable Multi-line Canvas Labels
    // Font scale adjusts gracefully with zoom
    const fontSize = Math.max(9, Math.min(14, 12 / Math.sqrt(globalScale)));
    ctx.font = `600 ${fontSize}px Inter, -apple-system, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    // Label Line 1: Vendor ID Pill
    const idText = node.id;
    const idMetrics = ctx.measureText(idText);
    const pad = 3;

    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.fillRect(
      node.x - idMetrics.width / 2 - pad,
      node.y + r + 3,
      idMetrics.width + pad * 2,
      fontSize + 2
    );

    ctx.fillStyle = isTarget ? '#fbbf24' : (isSelected ? '#93c5fd' : '#f8fafc');
    ctx.fillText(idText, node.x, node.y + r + 4);

    // Label Line 2: Company Name (shown when zoomed in enough)
    if (globalScale > 0.65) {
      const subFontSize = Math.max(8, Math.min(11, 10 / Math.sqrt(globalScale)));
      ctx.font = `400 ${subFontSize}px Inter, -apple-system, sans-serif`;

      let nameText = (node.label || '').replace(`(${node.id})`, '').trim();
      if (nameText.length > 18) nameText = nameText.substring(0, 16) + '…';

      if (nameText) {
        const nameMetrics = ctx.measureText(nameText);
        ctx.fillStyle = 'rgba(15, 23, 42, 0.75)';
        ctx.fillRect(
          node.x - nameMetrics.width / 2 - 2,
          node.y + r + fontSize + 6,
          nameMetrics.width + 4,
          subFontSize + 2
        );
        ctx.fillStyle = '#94a3b8';
        ctx.fillText(nameText, node.x, node.y + r + fontSize + 7);
      }
    }
  }, [selectedNode, hoverNode]);

  // Custom Edge Canvas Painting: Value-scaled Width + Pill Badges + Directional Flow
  const drawLink = useCallback((link, ctx, globalScale) => {
    const start = link.source;
    const end = link.target;
    if (!start || !end || typeof start.x !== 'number' || typeof end.x !== 'number') return;

    const isRecip = link.is_reciprocal;
    const isSelected = selectedNode && (
      (start.id === selectedNode.id) || (end.id === selectedNode.id)
    );
    const isHovered = hoverLink && (
      (hoverLink.source?.id || hoverLink.source) === (start.id || start) &&
      (hoverLink.target?.id || hoverLink.target) === (end.id || end)
    );

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);

    // Scaled stroke width based on total transaction value
    const val = Number(link.total_value) || 0;
    let strokeW = 1.4;
    if (val > 1000000) strokeW = 3.8;
    else if (val > 250000) strokeW = 2.6;
    else if (val > 50000) strokeW = 1.9;

    if (isRecip) strokeW = Math.max(strokeW, 2.5);
    if (isSelected || isHovered) strokeW += 1.8;

    ctx.lineWidth = strokeW;

    if (isRecip) {
      // Reciprocal / Bilateral tie: distinct violet dashed pattern
      ctx.strokeStyle = isHovered ? '#c084fc' : 'rgba(168, 85, 247, 0.85)';
      ctx.setLineDash([5, 3]);
    } else if (isHovered || isSelected) {
      ctx.strokeStyle = '#60a5fa';
    } else {
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.38)';
    }

    ctx.stroke();
    ctx.restore();

    // Draw Financial Badge on Edge Midpoint
    if (globalScale > 0.72 || isRecip || isHovered || isSelected) {
      const midX = (start.x + end.x) / 2;
      const midY = (start.y + end.y) / 2;
      const badgeText = `${formatINR(link.total_value)} (${link.invoice_count || 1} inv)`;

      const badgeFont = Math.max(7.5, Math.min(11, 9.5 / Math.sqrt(globalScale)));
      ctx.font = `500 ${badgeFont}px Inter, sans-serif`;
      const textW = ctx.measureText(badgeText).width;
      const pad = 3.5;

      ctx.fillStyle = isRecip ? 'rgba(88, 28, 135, 0.92)' : 'rgba(15, 23, 42, 0.88)';
      ctx.strokeStyle = isRecip ? '#c084fc' : (isSelected ? '#60a5fa' : 'rgba(100, 116, 139, 0.5)');
      ctx.lineWidth = 1;

      ctx.fillRect(midX - textW / 2 - pad, midY - badgeFont / 2 - pad, textW + pad * 2, badgeFont + pad * 2);
      ctx.strokeRect(midX - textW / 2 - pad, midY - badgeFont / 2 - pad, textW + pad * 2, badgeFont + pad * 2);

      ctx.fillStyle = isRecip ? '#f3e8ff' : '#f1f5f9';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(badgeText, midX, midY);
    }
  }, [selectedNode, hoverLink]);

  // Clickable pointer area sizing
  const nodePointerAreaPaint = useCallback((node, color, ctx) => {
    const r = (node.is_target ? 14 : 9) + 8;
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  }, []);

  // Compute Direct Trade Breakdown between selected counterparty and focal vendor
  const directTradeInfo = useMemo(() => {
    if (!selectedNode || selectedNode.is_target || !graphData?.edges) return null;

    const inwardEdges = graphData.edges.filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source;
      const t = typeof e.target === 'object' ? e.target.id : e.target;
      return s === selectedNode.id && t === vendorId;
    });

    const outwardEdges = graphData.edges.filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source;
      const t = typeof e.target === 'object' ? e.target.id : e.target;
      return s === vendorId && t === selectedNode.id;
    });

    const inwardVal = inwardEdges.reduce((acc, e) => acc + (Number(e.total_value) || 0), 0);
    const outwardVal = outwardEdges.reduce((acc, e) => acc + (Number(e.total_value) || 0), 0);
    const inwardInv = inwardEdges.reduce((acc, e) => acc + (Number(e.invoice_count) || 0), 0);
    const outwardInv = outwardEdges.reduce((acc, e) => acc + (Number(e.invoice_count) || 0), 0);

    return {
      hasInward: inwardEdges.length > 0,
      hasOutward: outwardEdges.length > 0,
      inwardVal,
      outwardVal,
      inwardInv,
      outwardInv,
      isBilateral: inwardEdges.length > 0 && outwardEdges.length > 0
    };
  }, [selectedNode, vendorId, graphData]);

  return (
    <div className="graph-explorer-page">
      {/* Header */}
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>🕸️ Knowledge Graph Investigation Explorer</h2>
            <p>Commercial Trade Topology, Reciprocal Ties & Network Concentration Context</p>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-outline flex items-center gap-1" onClick={loadGraph}>
              <RefreshCw size={13} /> Reload Snapshot
            </button>
          </div>
        </div>
      </div>

      <ResearchDisclaimer compact />

      {/* Control Bar: Vendor, Depth, Period */}
      <div className="graph-toolbar">
        {/* Vendor Search Input & Quick Presets */}
        <div className="toolbar-group flex-wrap">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
            <Search size={15} className="text-muted" />
            <input
              type="text"
              className="filter-input"
              style={{ width: '160px', minWidth: '130px' }}
              placeholder="Vendor ID (e.g. V0001)"
              value={vendorInput}
              onChange={(e) => setVendorInput(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-sm">Find</button>
          </form>

          {/* Quick vendor presets */}
          <div className="flex items-center gap-1 text-xs text-muted" style={{ marginLeft: '8px' }}>
            <span style={{ marginRight: '2px' }}>Presets:</span>
            {['V0001', 'V0002', 'V0003', 'V0005', 'V0010'].map((v) => (
              <button
                key={v}
                className={`badge-tag ${vendorId === v ? 'active-tag' : ''}`}
                onClick={() => {
                  setVendorId(v);
                  setVendorInput(v);
                }}
              >
                {v}
              </button>
            ))}
          </div>
        </div>

        {/* Depth & Temporal Boundary Selectors */}
        <div className="toolbar-group flex-wrap">
          {/* Depth Selector */}
          <div className="flex items-center gap-2" style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '4px 10px', borderRadius: '8px', border: '1px solid var(--border-primary)' }}>
            <Layers size={14} className="text-muted" />
            <span className="text-xs text-muted">Depth:</span>
            <button
              className={`btn btn-sm ${depth === 1 ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setDepth(1)}
              title="Immediate direct suppliers and buyers"
            >
              1 (Direct)
            </button>
            <button
              className={`btn btn-sm ${depth === 2 ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setDepth(2)}
              title="Multi-hop extended supply network"
            >
              2 (Multi-Hop)
            </button>
          </div>

          {/* Temporal Cutoff Selector */}
          <div className="flex items-center gap-2">
            <Calendar size={15} className="text-muted" />
            <span className="text-xs text-muted">Temporal Boundary:</span>
            <select
              className="filter-select"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              {AVAILABLE_PERIODS.map((p) => (
                <option key={p} value={p}>
                  t ≤ {p}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Sub-Toolbar: Layout Mode & Filter Chips */}
      <div className="graph-sub-toolbar mb-3">
        {/* Layout Mode Switcher */}
        <div className="flex items-center gap-2">
          <Sliders size={14} className="text-accent" />
          <span className="text-xs font-semibold">Layout:</span>
          <div className="segmented-control">
            <button
              className={`segmented-btn ${layoutMode === 'concentric' ? 'active' : ''}`}
              onClick={() => setLayoutMode('concentric')}
              title="Concentric Structured: Focal entity centered, suppliers left, customers right"
            >
              🎯 Concentric (Organized)
            </button>
            <button
              className={`segmented-btn ${layoutMode === 'force' ? 'active' : ''}`}
              onClick={() => setLayoutMode('force')}
              title="Force-Directed: Free organic physics simulation"
            >
              🌐 Force Physics
            </button>
          </div>
        </div>

        {/* Counterparty Filter Chips */}
        <div className="flex items-center gap-2 flex-wrap">
          <Filter size={14} className="text-muted" />
          <span className="text-xs text-muted">Filter:</span>
          {[
            { key: 'ALL', label: 'All Counterparties' },
            { key: 'SUPPLIERS', label: 'Suppliers (Inward)' },
            { key: 'CUSTOMERS', label: 'Customers (Outward)' },
            { key: 'RECIPROCAL', label: 'Reciprocal Ties' },
            { key: 'HIGH_RISK', label: 'High Risk Only' },
          ].map(f => (
            <button
              key={f.key}
              className={`filter-chip ${filterType === f.key ? 'active' : ''}`}
              onClick={() => setFilterType(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Temporal Boundary Notice */}
      <div className="mb-3 p-2.5 border rounded-md flex items-center justify-between text-xs" style={{ background: 'rgba(59, 130, 246, 0.05)', borderColor: 'rgba(59, 130, 246, 0.2)' }}>
        <div className="flex items-center gap-2">
          <Info size={15} className="text-info" />
          <span>
            <strong>Temporal Boundary Enforced:</strong> Relationships strictly observe{' '}
            <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 5px', borderRadius: '4px' }}>tax_period ≤ {period}</code>. Zero future relationship leakage.
          </span>
        </div>
        <span className="badge info">Causality Protected</span>
      </div>

      {/* Main Grid: Graph Canvas + Side Investigation Panel */}
      <div className="graph-layout-grid">
        {/* Force Graph Canvas Card */}
        <div className="card" ref={containerRef} style={{ minHeight: '620px', position: 'relative' }}>
          {/* Card Header with Counts & Navigation Controls */}
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Network size={18} className="text-accent" />
              <span className="font-semibold text-sm">
                Trading Topology Subgraph ({processedGraphData.nodes.length} Nodes, {processedGraphData.links.length} Edges)
              </span>
              {layoutMode === 'concentric' && (
                <span className="badge info text-xs" style={{ fontSize: '0.65rem' }}>
                  Suppliers (Left) ➔ Center ➔ Customers (Right)
                </span>
              )}
            </div>

            {/* Quick Canvas Navigation Controls */}
            <div className="flex items-center gap-1.5">
              <button
                className="btn btn-outline btn-xs p-1"
                onClick={handleZoomIn}
                title="Zoom In"
              >
                <ZoomIn size={13} />
              </button>
              <button
                className="btn btn-outline btn-xs p-1"
                onClick={handleZoomOut}
                title="Zoom Out"
              >
                <ZoomOut size={13} />
              </button>
              <button
                className="btn btn-outline btn-xs p-1"
                onClick={handleCenterFocal}
                title="Center on Focal Entity"
              >
                <Target size={13} />
              </button>
              <button
                className="btn btn-outline btn-xs flex items-center gap-1"
                onClick={handleFit}
                title="Fit entire graph in view"
              >
                <Maximize2 size={13} /> Fit
              </button>
            </div>
          </div>

          {loading ? (
            <div className="state-container state-loading" style={{ height: '520px' }}>
              <div className="spinner" />
              <p>Constructing time-safe topology snapshot for {vendorId}...</p>
            </div>
          ) : error ? (
            <div className="state-container state-error" style={{ height: '520px' }}>
              <AlertCircle size={36} className="error-icon" />
              <p>{error}</p>
              <button className="btn btn-primary mt-2" onClick={loadGraph}>Retry</button>
            </div>
          ) : processedGraphData.nodes.length === 0 ? (
            <div className="state-container state-empty" style={{ height: '520px' }}>
              <Network size={40} className="empty-icon text-muted mb-2" />
              <h4>No Graph Relationships Available</h4>
              <p className="text-muted text-xs">
                No recorded commercial supply links matching filter <strong>{filterType}</strong> for <strong>{vendorId}</strong> in period <strong>t ≤ {period}</strong>.
              </p>
              {filterType !== 'ALL' && (
                <button className="btn btn-outline btn-sm mt-2" onClick={() => setFilterType('ALL')}>
                  Reset Filter
                </button>
              )}
            </div>
          ) : (
            <div style={{ height: '540px', width: '100%', position: 'relative' }}>
              <ForceGraph2D
                ref={graphRef}
                width={dimensions.width - 32}
                height={540}
                graphData={processedGraphData}
                nodeId="id"
                nodeCanvasObject={drawNode}
                nodePointerAreaPaint={nodePointerAreaPaint}
                linkCanvasObject={drawLink}
                linkSource="source"
                linkTarget="target"
                linkDirectionalArrowLength={5}
                linkDirectionalArrowRelPos={0.82}
                linkDirectionalParticles={(link) => (link.is_reciprocal ? 3 : 1)}
                linkDirectionalParticleSpeed={(link) => (link.is_reciprocal ? 0.009 : 0.004)}
                linkDirectionalParticleWidth={(link) => (link.is_reciprocal ? 2.5 : 1.8)}
                linkDirectionalParticleColor={(link) => (link.is_reciprocal ? '#c084fc' : '#60a5fa')}
                onNodeClick={(node) => setSelectedNode(node)}
                onNodeHover={(node) => setHoverNode(node || null)}
                onLinkHover={(link) => setHoverLink(link || null)}
                cooldownTicks={layoutMode === 'concentric' ? 20 : 90}
                onEngineStop={() => {
                  if (layoutMode === 'concentric') {
                    graphRef.current?.zoomToFit(400, 45);
                  }
                }}
              />

              {/* In-Canvas Floating Legend */}
              <div className="graph-canvas-legend">
                <div className="legend-title">Graph Semantics</div>
                <div className="legend-row">
                  <span className="legend-bullet" style={{ background: '#f59e0b' }} />
                  <span>Target Focal Vendor</span>
                </div>
                <div className="legend-row">
                  <span className="legend-bullet" style={{ background: '#06b6d4' }} />
                  <span>Supplier (Inward / GSTR-2B)</span>
                </div>
                <div className="legend-row">
                  <span className="legend-bullet" style={{ background: '#3b82f6' }} />
                  <span>Customer (Outward / GSTR-1)</span>
                </div>
                <div className="legend-row">
                  <span className="legend-bullet" style={{ background: '#8b5cf6' }} />
                  <span>Reciprocal Partner (Bilateral)</span>
                </div>
                <div className="legend-divider" />
                <div className="legend-sub">Outer Ring: Risk Band</div>
                <div className="flex gap-2 text-xs">
                  <span className="flex items-center gap-1"><span className="legend-dot" style={{ borderColor: '#ef4444' }} /> High</span>
                  <span className="flex items-center gap-1"><span className="legend-dot" style={{ borderColor: '#f59e0b' }} /> Med</span>
                  <span className="flex items-center gap-1"><span className="legend-dot" style={{ borderColor: '#10b981' }} /> Low</span>
                </div>
              </div>

              {/* Floating Hover Card for Node or Link */}
              {hoverNode && (
                <div className="graph-floating-hover-card">
                  <div className="font-bold text-xs text-primary">{hoverNode.label || hoverNode.id}</div>
                  <div className="text-muted text-xs">{hoverNode.id} • {hoverNode.gstin}</div>
                  <div className="mt-1 flex items-center justify-between text-xs">
                    <span className="text-muted">Network Role:</span>
                    <span className="font-semibold uppercase text-accent">{hoverNode.node_type}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted">Risk Score:</span>
                    <span className={`font-semibold ${hoverNode.risk_score >= 70 ? 'text-danger' : hoverNode.risk_score >= 35 ? 'text-warning' : 'text-success'}`}>
                      {Number(hoverNode.risk_score).toFixed(1)}/100 ({hoverNode.risk_band})
                    </span>
                  </div>
                  <div className="text-muted text-xs mt-1" style={{ fontSize: '0.68rem', fontStyle: 'italic' }}>
                    Click node to view trade relationship details.
                  </div>
                </div>
              )}

              {hoverLink && !hoverNode && (
                <div className="graph-floating-hover-card">
                  <div className="font-bold text-xs text-primary">Commercial Trade Edge</div>
                  <div className="text-xs text-muted">
                    {(hoverLink.source?.id || hoverLink.source)} ➔ {(hoverLink.target?.id || hoverLink.target)}
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs">
                    <span className="text-muted">Taxable Value:</span>
                    <strong>{formatINR(hoverLink.total_value)}</strong>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted">Total GST Tax:</span>
                    <span>{formatINR(hoverLink.total_tax)}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted">Invoices:</span>
                    <span>{hoverLink.invoice_count} invoices</span>
                  </div>
                  {hoverLink.is_reciprocal && (
                    <div className="mt-1 text-xs text-warning flex items-center gap-1">
                      <Repeat size={12} /> Bilateral / Reciprocal Trade Link
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Side Panel: Investigation Signals, Trade Breakdown & Guide */}
        <div className="graph-side-panel">
          {/* Selected Node or Focal Vendor Inspector */}
          <div className="card">
            <div className="card-header flex items-center justify-between">
              <h3>{selectedNode ? '📌 Selected Counterparty' : '🎯 Investigation Focal Entity'}</h3>
              {selectedNode && (
                <button
                  className="btn btn-ghost btn-xs text-muted"
                  onClick={() => setSelectedNode(null)}
                  title="Clear selection"
                >
                  Clear
                </button>
              )}
            </div>

            {selectedNode ? (
              <div className="text-xs">
                <div className="font-bold text-sm text-primary mb-1">{selectedNode.label}</div>
                <div className="text-muted mb-2">{selectedNode.id} • {selectedNode.gstin}</div>

                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Network Role:</span>
                  <span className="font-semibold uppercase text-accent">{selectedNode.node_type}</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Network Degree:</span>
                  <span>{selectedNode.degree || 0} connected ties ({selectedNode.in_degree || 0} In / {selectedNode.out_degree || 0} Out)</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Risk Band:</span>
                  <span className={`badge-${selectedNode.risk_band?.toLowerCase() || 'low'}`}>
                    {selectedNode.risk_band} ({Number(selectedNode.risk_score || 0).toFixed(1)})
                  </span>
                </div>

                {/* Direct Relationship with Focal Entity */}
                {directTradeInfo && (
                  <div className="mt-3 p-2.5 rounded-md" style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-primary)' }}>
                    <div className="font-semibold text-xs mb-1 text-accent flex items-center gap-1">
                      <ArrowRight size={12} /> Direct Trade with Focal Entity ({vendorId})
                    </div>
                    {directTradeInfo.hasInward && (
                      <div className="flex items-center justify-between py-0.5">
                        <span className="text-muted flex items-center gap-1">
                          <ArrowDownLeft size={11} className="text-info" /> Supplies to {vendorId}:
                        </span>
                        <strong>{formatINR(directTradeInfo.inwardVal)} ({directTradeInfo.inwardInv} inv)</strong>
                      </div>
                    )}
                    {directTradeInfo.hasOutward && (
                      <div className="flex items-center justify-between py-0.5">
                        <span className="text-muted flex items-center gap-1">
                          <ArrowUpRight size={11} className="text-primary" /> Purchases from {vendorId}:
                        </span>
                        <strong>{formatINR(directTradeInfo.outwardVal)} ({directTradeInfo.outwardInv} inv)</strong>
                      </div>
                    )}
                    {directTradeInfo.isBilateral && (
                      <div className="mt-1.5 p-1.5 rounded text-warning text-xs flex items-center gap-1" style={{ background: 'rgba(168, 85, 247, 0.1)', border: '1px solid rgba(168, 85, 247, 0.25)' }}>
                        <Repeat size={12} />
                        <span><strong>Reciprocal Tie:</strong> Both buy & sell with each other</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Quick Action Buttons */}
                <div className="mt-3 flex gap-2">
                  <button
                    className="btn btn-sm btn-outline flex-1 flex items-center justify-center gap-1"
                    onClick={() => handleRecenter(selectedNode.id)}
                    title="Make this vendor the center focal entity of the graph"
                  >
                    <Target size={13} /> Re-Center Graph
                  </button>
                  <button
                    className="btn btn-sm btn-primary flex-1 flex items-center justify-center gap-1"
                    onClick={() => navigate(`/investigation/${selectedNode.id}`)}
                    title="Open in Unified Investigation Workspace"
                  >
                    <ExternalLink size={13} /> Investigate
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-xs">
                <div className="font-bold text-sm text-primary mb-1">Focal Entity: {vendorId}</div>
                <p className="text-muted mb-2">Click any counterparty node or link on the canvas to inspect relationship and trade details.</p>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Exploration Depth:</span>
                  <span>Depth {depth} ({depth === 1 ? 'Direct Tier-1' : 'Multi-Hop Extended'})</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Visible Counterparties:</span>
                  <span>{processedGraphData.nodes.length > 0 ? processedGraphData.nodes.length - 1 : 0} nodes</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-muted">Reciprocal Pairs:</span>
                  <span className={graphData?.metadata?.reciprocal_count > 0 ? 'text-warning font-semibold' : ''}>
                    {graphData?.metadata?.reciprocal_count || 0} ties
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Trade Concentration Metrics */}
          <div className="card">
            <div className="card-header">
              <h3>📊 Counterparty Concentration</h3>
            </div>
            <div className="text-xs flex flex-col gap-2">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted">Supplier Concentration:</span>
                  <strong className={graphData?.metadata?.supplier_concentration_pct > 80 ? 'text-danger' : ''}>
                    {graphData?.metadata?.supplier_concentration_pct || 0}%
                  </strong>
                </div>
                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(graphData?.metadata?.supplier_concentration_pct || 0, 100)}%`, height: '100%', background: graphData?.metadata?.supplier_concentration_pct > 80 ? '#ef4444' : '#06b6d4' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted">Customer Concentration:</span>
                  <strong className={graphData?.metadata?.customer_concentration_pct > 80 ? 'text-danger' : ''}>
                    {graphData?.metadata?.customer_concentration_pct || 0}%
                  </strong>
                </div>
                <div className="progress-bar-bg" style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(graphData?.metadata?.customer_concentration_pct || 0, 100)}%`, height: '100%', background: graphData?.metadata?.customer_concentration_pct > 80 ? '#ef4444' : '#3b82f6' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Structural Network Flags (Objective) */}
          <div className="card">
            <div className="card-header">
              <h3>🚩 Structural Network Flags</h3>
            </div>
            {graphData?.metadata?.network_flags?.length === 0 ? (
              <p className="text-xs text-muted">No high-concentration or cyclical trading patterns identified for this period.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {graphData?.metadata?.network_flags?.map((flag, idx) => (
                  <div key={idx} className="p-2 border rounded text-xs" style={{ background: 'rgba(245, 158, 11, 0.05)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                    <div className="font-semibold text-warning mb-1">Topology Signal</div>
                    <div className="text-muted">{flag}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Collapsible Plain-English Auditor Guide */}
          <div className="card">
            <div
              className="card-header flex items-center justify-between cursor-pointer"
              onClick={() => setGuideOpen(!guideOpen)}
              style={{ paddingBottom: guideOpen ? '12px' : '0' }}
            >
              <div className="flex items-center gap-1.5">
                <HelpCircle size={15} className="text-accent" />
                <h3 style={{ margin: 0 }}>How to Read This Graph</h3>
              </div>
              {guideOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {guideOpen && (
              <div className="text-xs text-muted flex flex-col gap-2.5 pt-1">
                <div>
                  <strong className="text-primary block">Arrow Direction (A ➔ B):</strong>
                  Indicates commercial supply flow. Entity A issued outward supply invoices (GSTR-1), and Entity B claimed inward Input Tax Credit (GSTR-2B).
                </div>
                <div>
                  <strong className="text-warning block">🟣 Reciprocal Bilateral Links (A ⇄ B):</strong>
                  Both entities issue invoices to each other in the same audit period. Often scrutinized for circular billing, accommodation entries, or synthetic turnover.
                </div>
                <div>
                  <strong className="text-info block">🎯 Concentric Layout:</strong>
                  Positions suppliers on the left and customers on the right, providing an intuitive left-to-right supply chain progression.
                </div>
                <div>
                  <strong className="text-danger block">Ring Color (Risk Level):</strong>
                  Red indicates high risk (compliance or default score ≥ 70), Amber is medium (35–69), and Green is compliant (&lt; 35).
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
