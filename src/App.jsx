import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Network,
  GitCompare,
  ShieldAlert,
  FileSearch,
  Users,
  Database,
  Activity,
  Settings as SettingsIcon,
  Sun,
  Moon,
  LogOut,
  PlusCircle,
  BookOpen,
  DollarSign,
  PanelLeftClose,
  PanelLeft
} from 'lucide-react';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider, useData } from './context/DataContext';

import Dashboard from './pages/Dashboard';
import VendorRiskTable from './pages/VendorRiskTable';
import VendorDetail from './pages/VendorDetail';
import KnowledgeGraph from './pages/KnowledgeGraph';
import KnowledgeGraphExplorer from './pages/KnowledgeGraphExplorer';
import InvestigationWorkspace from './pages/InvestigationWorkspace';
import ITCExposureAnalytics from './pages/ITCExposureAnalytics';
import Methodology from './pages/Methodology';

import Reconciliation from './pages/Reconciliation';
import AuditTrails from './pages/AuditTrails';
import VendorCompliance from './pages/VendorCompliance';
import Settings from './pages/Settings';
import LoginPage from './pages/LoginPage';
import DataEntry from './pages/DataEntry';
import './App.css';

function ThemeToggleButton({ collapsed = false }) {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      type="button"
      className="theme-toggle-btn"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      data-tooltip={collapsed ? `${theme === 'dark' ? 'Light' : 'Dark'} Mode` : undefined}
    >
      {theme === 'dark' ? <Sun size={18} strokeWidth={2.2} /> : <Moon size={18} strokeWidth={2.2} />}
    </button>
  );
}

function Sidebar({ collapsed, toggleSidebar }) {
  const { user, logout } = useAuth();
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className={`sidebar-logo ${collapsed ? 'collapsed' : ''}`}>
        {!collapsed && (
          <div className="sidebar-brand">
            <h1>⚡ GST ReconcileAI</h1>
            <p>Risk Intelligence & Knowledge Graph</p>
          </div>
        )}
        <button
          type="button"
          className="sidebar-toggle-btn"
          onClick={toggleSidebar}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeft size={18} strokeWidth={2} /> : <PanelLeftClose size={18} strokeWidth={2} />}
        </button>
      </div>

      {/* User info */}
      <div className={`sidebar-user ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-avatar" title={`${user?.name || 'User'} (${user?.role || 'Guest'})`}>
          {user?.name?.charAt(0).toUpperCase() || 'U'}
        </div>
        {!collapsed && (
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">{user?.name}</span>
            <span className="sidebar-user-role">{user?.role}</span>
          </div>
        )}
        <ThemeToggleButton collapsed={collapsed} />
      </div>

      <nav className="sidebar-nav">
        {!collapsed ? (
          <div className="nav-section-label">Risk Intelligence</div>
        ) : (
          <div className="sidebar-nav-divider" />
        )}
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Dashboard">
          <LayoutDashboard className="nav-icon nav-icon-dashboard" />
          {!collapsed && <span className="nav-label">Dashboard</span>}
        </NavLink>
        <NavLink to="/vendors" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Vendor Risk Directory">
          <Users className="nav-icon nav-icon-vendors" />
          {!collapsed && <span className="nav-label">Vendor Risk Directory</span>}
        </NavLink>
        <NavLink to="/investigation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Investigation Workspace">
          <FileSearch className="nav-icon nav-icon-investigation" />
          {!collapsed && <span className="nav-label">Investigation Workspace</span>}
        </NavLink>
        <NavLink to="/itc-exposure" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="ITC Exposure Analytics">
          <DollarSign className="nav-icon nav-icon-itc" />
          {!collapsed && <span className="nav-label">ITC Exposure Analytics</span>}
        </NavLink>
        <NavLink to="/graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Knowledge Graph">
          <Network className="nav-icon nav-icon-graph" />
          {!collapsed && <span className="nav-label">Knowledge Graph</span>}
        </NavLink>

        {!collapsed ? (
          <div className="nav-section-label">Reconciliation & Compliance</div>
        ) : (
          <div className="sidebar-nav-divider" />
        )}
        <NavLink to="/reconciliation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Reconciliation">
          <GitCompare className="nav-icon nav-icon-reconciliation" />
          {!collapsed && <span className="nav-label">Reconciliation</span>}
        </NavLink>
        <NavLink to="/vendor-compliance" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Vendor Compliance">
          <ShieldAlert className="nav-icon nav-icon-compliance" />
          {!collapsed && <span className="nav-label">Vendor Compliance</span>}
        </NavLink>
        <NavLink to="/audit-trails" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Audit Trails">
          <Activity className="nav-icon nav-icon-audit" />
          {!collapsed && <span className="nav-label">Audit Trails</span>}
        </NavLink>

        {!collapsed ? (
          <div className="nav-section-label">System & Tools</div>
        ) : (
          <div className="sidebar-nav-divider" />
        )}
        <NavLink to="/data-entry" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Data Entry">
          <PlusCircle className="nav-icon nav-icon-data-entry" />
          {!collapsed && <span className="nav-label">Data Entry</span>}
        </NavLink>
        <NavLink to="/methodology" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Methodology & ML Spec">
          <BookOpen className="nav-icon nav-icon-methodology" />
          {!collapsed && <span className="nav-label">Methodology & ML Spec</span>}
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} data-tooltip="Settings">
          <SettingsIcon className="nav-icon nav-icon-settings" />
          {!collapsed && <span className="nav-label">Settings</span>}
        </NavLink>
      </nav>

      <SystemStatus collapsed={collapsed} />
    </aside>
  );
}

function SystemStatus({ collapsed = false }) {
  const { apiOnline, graphStatus, modelInfo } = useData();

  if (collapsed) {
    return (
      <div className="sidebar-footer collapsed" title={apiOnline ? 'API & Backend Online' : 'API Offline (Fallback)'}>
        <div className="status-indicator-compact">
          <span className="status-dot" style={{ background: apiOnline ? '#22c55e' : '#ef4444' }}></span>
        </div>
      </div>
    );
  }

  // These reflect what the backend reports, not what we hope is running - a
  // hardcoded green dot hides exactly the outages this panel exists to surface.
  const graphConnected = Boolean(graphStatus?.connected);
  const modelSource = modelInfo?.available ? modelInfo.source : null;

  const rows = [
    {
      icon: <Database size={14} />,
      label: apiOnline ? 'API & Backend Online' : 'API Offline (Fallback)',
      ok: apiOnline,
      title: apiOnline ? 'FastAPI & Data Store reachable' : 'Backend unreachable',
    },
    {
      icon: <Network size={14} />,
      label: graphConnected ? 'Graph Engine Active' : 'Graph Engine Offline',
      ok: graphConnected,
      title: graphConnected
        ? `Neo4j reachable at ${graphStatus.uri || 'the configured endpoint'}`
        : `Neo4j unavailable: ${graphStatus?.reason || 'not checked'}`,
    },
    {
      icon: <Activity size={14} />,
      label: modelSource ? 'Risk Model Active' : 'Risk Model Unavailable',
      ok: Boolean(modelSource),
      title: modelSource
        ? `Vendor risk scoring: ${modelSource}`
        : 'Backend reported no trained model; heuristic fallback in use',
    },
  ];

  return (
    <div className="sidebar-footer">
      {rows.map((row, i) => (
        <div className="status-indicator" key={i} style={i ? { marginTop: '8px' } : undefined} title={row.title}>
          {row.icon}
          <span>{row.label}</span>
          <span className="status-dot" style={{ background: row.ok ? '#22c55e' : '#ef4444' }}></span>
        </div>
      ))}
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('gst-sidebar-collapsed') === 'true';
  });

  const toggleSidebar = () => {
    setCollapsed(prev => {
      const next = !prev;
      localStorage.setItem('gst-sidebar-collapsed', String(next));
      return next;
    });
  };

  if (loading) return null;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage initialMode="login" />} />
        <Route path="/register" element={<LoginPage initialMode="signup" />} />
        <Route path="/signup" element={<LoginPage initialMode="signup" />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className={`app-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar collapsed={collapsed} toggleSidebar={toggleSidebar} />
      <main className="main-content">
        <div className="page-content">
          <Routes>
            {/* Dashboard routes */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />

            {/* Vendor Risk Directory & Detail */}
            <Route path="/vendors" element={<VendorRiskTable />} />
            <Route path="/vendors/:vendor_id" element={<VendorDetail />} />

            {/* Unified Investigation Workspace */}
            <Route path="/investigation" element={<InvestigationWorkspace />} />
            <Route path="/investigation/:vendor_id" element={<InvestigationWorkspace />} />

            {/* ITC Exposure Analytics */}
            <Route path="/itc-exposure" element={<ITCExposureAnalytics />} />
            <Route path="/itc-risk" element={<ITCExposureAnalytics />} />

            {/* Knowledge Graph Explorer */}
            <Route path="/graph" element={<KnowledgeGraph />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
            <Route path="/graph-explorer" element={<KnowledgeGraphExplorer />} />

            {/* Reconciliation */}
            <Route path="/reconciliation" element={<Reconciliation />} />

            {/* Research Methodology */}
            <Route path="/methodology" element={<Methodology />} />

            {/* Preserved existing routes */}
            <Route path="/audit-trails" element={<AuditTrails />} />
            <Route path="/vendor-compliance" element={<VendorCompliance />} />
            <Route path="/data-entry" element={<DataEntry />} />
            <Route path="/settings" element={<Settings />} />

            {/* Fallback & Auth redirects */}
            <Route path="/login" element={<Navigate to="/" replace />} />
            <Route path="/register" element={<Navigate to="/" replace />} />
            <Route path="/signup" element={<Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <DataProvider>
            <AppContent />
          </DataProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
