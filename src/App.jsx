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
  DollarSign
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

function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      type="button"
      className="theme-toggle-btn"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? <Sun size={18} strokeWidth={2.2} /> : <Moon size={18} strokeWidth={2.2} />}
    </button>
  );
}

function Sidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>⚡ GST ReconcileAI</h1>
        <p>Risk Intelligence & Knowledge Graph</p>
      </div>

      {/* User info */}
      <div className="sidebar-user">
        <div className="sidebar-avatar">{user?.name?.charAt(0).toUpperCase() || 'U'}</div>
        <div className="sidebar-user-info">
          <span className="sidebar-user-name">{user?.name}</span>
          <span className="sidebar-user-role">{user?.role}</span>
        </div>
        <ThemeToggleButton />
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Risk Intelligence</div>
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard className="nav-icon" />
          Dashboard
        </NavLink>
        <NavLink to="/vendors" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Users className="nav-icon" />
          Vendor Risk Directory
        </NavLink>
        <NavLink to="/investigation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <FileSearch className="nav-icon" />
          Investigation Workspace
        </NavLink>
        <NavLink to="/itc-exposure" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <DollarSign className="nav-icon" />
          ITC Exposure Analytics
        </NavLink>
        <NavLink to="/graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Network className="nav-icon" />
          Knowledge Graph
        </NavLink>

        <div className="nav-section-label">Reconciliation & Compliance</div>
        <NavLink to="/reconciliation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <GitCompare className="nav-icon" />
          Reconciliation
        </NavLink>
        <NavLink to="/vendor-compliance" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <ShieldAlert className="nav-icon" />
          Vendor Compliance
        </NavLink>
        <NavLink to="/audit-trails" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Activity className="nav-icon" />
          Audit Trails
        </NavLink>

        <div className="nav-section-label">System & Tools</div>
        <NavLink to="/data-entry" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <PlusCircle className="nav-icon" />
          Data Entry
        </NavLink>
        <NavLink to="/methodology" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <BookOpen className="nav-icon" />
          Methodology & ML Spec
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <SettingsIcon className="nav-icon" />
          Settings
        </NavLink>
      </nav>

      <SystemStatus />
    </aside>
  );
}

function SystemStatus() {
  const { apiOnline, graphStatus, modelInfo } = useData();

  const rows = [
    {
      icon: <Database size={14} />,
      label: apiOnline ? 'API & Backend Online' : 'API Offline (Fallback)',
      ok: apiOnline,
      title: apiOnline ? 'FastAPI & Data Store reachable' : 'Backend unreachable',
    },
    {
      icon: <Network size={14} />,
      label: 'Graph Engine Active',
      ok: true,
      title: 'Time-safe Knowledge Graph investigation active',
    },
    {
      icon: <Activity size={14} />,
      label: 'Tabular XGBoost Loaded',
      ok: true,
      title: 'Frozen Tabular XGBoost (19 features, Tree SHAP) active',
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

  if (loading) return null;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar />
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

            {/* Fallback */}
            <Route path="/login" element={<Navigate to="/" replace />} />
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
