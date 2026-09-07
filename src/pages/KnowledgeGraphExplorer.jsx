import React, { useState, useEffect, useRef, useMemo } from 'react';
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
  Maximize2
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

  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 580 });

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
          height: 580,
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

  // Node color helper
  const getNodeColor = (node) => {
    if (node.is_target) return '#f59e0b'; // Amber for center
    if (node.node_type === 'reciprocal') return '#8b5cf6'; // Purple for reciprocal
    if (node.node_type === 'supplier') return '#06b6d4'; // Cyan
    if (node.node_type === 'customer') return '#3b82f6'; // Blue
    return '#64748b'; // Gray for peer
  };

  // Node size helper
  const getNodeSize = (node) => {
    if (node.is_target) return 10;
    if (node.node_type === 'reciprocal') return 7.5;
    return 6;
  };

  return (
    <div className="graph-explorer-page">
      {/* Header */}
      <div className="page-header mb-3">
        <div className="page-header-row">
          <div>
            <h2>🕸️ Knowledge Graph Investigation Explorer</h2>
            <p>Time-Safe Commercial Trade Topology, Reciprocal Ties & Network Concentration Context</p>
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

      {/* Temporal Cutoff Guarantee Notice */}
      <div className="mb-4 p-3 border rounded-md flex items-center justify-between text-xs" style={{ background: 'rgba(59, 130, 246, 0.06)', borderColor: 'rgba(59, 130, 246, 0.25)' }}>
        <div className="flex items-center gap-2">
          <Info size={16} className="text-info" />
          <span>
            <strong>Temporal Boundary Enforced:</strong> All graph edges and transaction volumes strictly observe{' '}
            <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px' }}>tax_period ≤ {period}</code>. Zero future relationship leakage.
          </span>
        </div>
        <span className="badge info">Causality Protected</span>
      </div>

      {/* Graph Display and Side Panel */}
      <div className="graph-layout-grid">
        {/* Force Graph Canvas Card */}
        <div className="card" ref={containerRef} style={{ minHeight: '600px', position: 'relative' }}>
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Network size={18} className="text-accent" />
              <span className="font-semibold text-sm">
                Trading Topology Subgraph ({graphData?.metadata?.total_nodes || 0} Nodes, {graphData?.metadata?.total_edges || 0} Edges)
              </span>
            </div>
            <button
              className="btn btn-outline btn-sm flex items-center gap-1"
              onClick={() => graphRef.current?.zoomToFit(400, 30)}
              title="Fit graph to view"
            >
              <Maximize2 size={13} /> Fit
            </button>
          </div>

          {loading ? (
            <div className="state-container state-loading" style={{ height: '500px' }}>
              <div className="spinner" />
              <p>Constructing time-safe topology snapshot for {vendorId}...</p>
            </div>
          ) : error ? (
            <div className="state-container state-error" style={{ height: '500px' }}>
              <AlertCircle size={36} className="error-icon" />
              <p>{error}</p>
              <button className="btn btn-primary mt-2" onClick={loadGraph}>Retry</button>
            </div>
          ) : graphData?.nodes?.length === 0 || (graphData?.nodes?.length === 1 && graphData?.edges?.length === 0) ? (
            <div className="state-container state-empty" style={{ height: '500px' }}>
              <Network size={40} className="empty-icon text-muted mb-2" />
              <h4>No Graph Relationships Available</h4>
              <p className="text-muted text-xs">
                No recorded commercial supply links for <strong>{vendorId}</strong> in period <strong>t ≤ {period}</strong>.
              </p>
            </div>
          ) : (
            <div style={{ height: '520px', width: '100%', position: 'relative' }}>
              <ForceGraph2D
                ref={graphRef}
                width={dimensions.width - 32}
                height={520}
                graphData={{
                  nodes: graphData?.nodes || [],
                  links: graphData?.edges || [],
                }}
                nodeId="id"
                nodeLabel={(node) => `${node.label} (${node.id})\nType: ${node.node_type}\nScore: ${node.risk_score}`}
                nodeColor={getNodeColor}
                nodeRelSize={1}
                nodeVal={getNodeSize}
                linkSource="source"
                linkTarget="target"
                linkColor={(link) => (link.is_reciprocal ? 'rgba(139, 92, 246, 0.7)' : 'rgba(255, 255, 255, 0.25)')}
                linkWidth={(link) => (link.is_reciprocal ? 2.5 : 1.2)}
                linkDirectionalArrowLength={4.5}
                linkDirectionalArrowRelPos={0.8}
                linkDirectionalParticles={1}
                linkDirectionalParticleSpeed={0.005}
                onNodeClick={(node) => setSelectedNode(node)}
                cooldownTicks={80}
                onEngineStop={() => graphRef.current?.zoomToFit(400, 30)}
              />

              {/* In-Canvas Graph Legend */}
              <div
                style={{
                  position: 'absolute',
                  bottom: '12px',
                  left: '12px',
                  background: 'rgba(26, 32, 53, 0.85)',
                  border: '1px solid var(--border-primary)',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  fontSize: '0.72rem',
                  display: 'flex',
                  gap: '12px',
                  backdropFilter: 'blur(4px)',
                }}
              >
                <span className="flex items-center gap-1"><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }} /> Target Vendor</span>
                <span className="flex items-center gap-1"><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#06b6d4' }} /> Supplier</span>
                <span className="flex items-center gap-1"><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }} /> Customer</span>
                <span className="flex items-center gap-1"><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8b5cf6' }} /> Reciprocal Partner</span>
              </div>
            </div>
          )}
        </div>

        {/* Side Panel: Investigation Signals & Concentration Details */}
        <div className="graph-side-panel">
          {/* Selected Node or Center Summary */}
          <div className="card">
            <div className="card-header">
              <h3>{selectedNode ? '📌 Selected Counterparty' : '🎯 Investigation Focal Entity'}</h3>
            </div>

            {selectedNode ? (
              <div className="text-xs">
                <div className="font-bold text-sm text-primary mb-1">{selectedNode.label}</div>
                <div className="text-muted mb-2">{selectedNode.id} • {selectedNode.gstin}</div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Network Role:</span>
                  <span className="font-semibold uppercase">{selectedNode.node_type}</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Network Degree:</span>
                  <span>{selectedNode.degree} connected ties</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Risk Band:</span>
                  <span className={`badge-${selectedNode.risk_band?.toLowerCase() || 'low'}`}>{selectedNode.risk_band}</span>
                </div>
                <div className="mt-3 flex gap-2">
                  <button
                    className="btn btn-sm btn-outline flex-1"
                    onClick={() => {
                      setVendorId(selectedNode.id);
                      setVendorInput(selectedNode.id);
                    }}
                  >
                    Center On Node
                  </button>
                  <button
                    className="btn btn-sm btn-primary flex-1"
                    onClick={() => navigate(`/investigation/${selectedNode.id}`)}
                  >
                    Investigate
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-xs">
                <div className="font-bold text-sm text-primary mb-1">Center Vendor: {vendorId}</div>
                <p className="text-muted mb-2">Click any counterparty node on the graph canvas to inspect its trade connections.</p>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Exploration Depth:</span>
                  <span>Depth {depth}</span>
                </div>
                <div className="flex justify-between py-1 border-bottom">
                  <span className="text-muted">Active Neighbors:</span>
                  <span>{graphData?.nodes?.length ? graphData.nodes.length - 1 : 0} nodes</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-muted">Reciprocal Pairs:</span>
                  <span>{graphData?.metadata?.reciprocal_count || 0} ties</span>
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
                  <strong>{graphData?.metadata?.supplier_concentration_pct || 0}%</strong>
                </div>
                <div className="progress-bar-bg" style={{ height: '5px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(graphData?.metadata?.supplier_concentration_pct || 0, 100)}%`, height: '100%', background: '#06b6d4' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-muted">Customer Concentration:</span>
                  <strong>{graphData?.metadata?.customer_concentration_pct || 0}%</strong>
                </div>
                <div className="progress-bar-bg" style={{ height: '5px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${Math.min(graphData?.metadata?.customer_concentration_pct || 0, 100)}%`, height: '100%', background: '#3b82f6' }} />
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
        </div>
      </div>
    </div>
  );
}
