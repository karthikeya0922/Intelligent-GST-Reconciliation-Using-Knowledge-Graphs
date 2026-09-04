import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { LayoutDashboard, Network, GitCompare, ShieldAlert, FileSearch, Users, Database, Activity, Settings as SettingsIcon, Sun, Moon, LogOut, PlusCircle } from 'lucide-react';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider, useData } from './context/DataContext';
import Dashboard from './pages/Dashboard';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Reconciliation from './pages/Reconciliation';
import ITCRisk from './pages/ITCRisk';
import AuditTrails from './pages/AuditTrails';
import VendorCompliance from './pages/VendorCompliance';
import Settings from './pages/Settings';
import LoginPage from './pages/LoginPage';
import DataEntry from './pages/DataEntry';
import './App.css';

function ThemeToggleButton() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button className="theme-toggle-btn" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}

function Sidebar() {
  const { user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>⚡ GST ReconcileAI</h1>
        <p>Knowledge Graph Engine</p>
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
        <div className="nav-section-label">Overview</div>
        <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <LayoutDashboard className="nav-icon" />
          Dashboard
        </NavLink>

        <div className="nav-section-label">Deliverables</div>
        <NavLink to="/knowledge-graph" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Network className="nav-icon" />
          Knowledge Graph
        </NavLink>
        <NavLink to="/reconciliation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <GitCompare className="nav-icon" />
          Reconciliation
        </NavLink>
        <NavLink to="/itc-risk" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <ShieldAlert className="nav-icon" />
          ITC Risk Dashboard
        </NavLink>
        <NavLink to="/audit-trails" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <FileSearch className="nav-icon" />
          Audit Trails
        </NavLink>
        <NavLink to="/vendor-compliance" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <Users className="nav-icon" />
          Vendor Compliance
        </NavLink>

        <div className="nav-section-label">Tools</div>
        <NavLink to="/data-entry" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <PlusCircle className="nav-icon" />
          Data Entry
        </NavLink>

        <div className="nav-section-label">System</div>
        <NavLink to="/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <SettingsIcon className="nav-icon" />
          Settings
        </NavLink>
      </nav>

      <SystemStatus />
    </aside>
  );
}

// Live service status. These used to be hardcoded "connected" labels; they now
// reflect what the API actually reports, so the sidebar cannot claim a graph or
// model that is not running.
function SystemStatus() {
  const { apiOnline, graphStatus, modelInfo } = useData();

  const rows = [
    {
      icon: <Database size={14} />,
      label: apiOnline ? 'MongoDB Connected' : 'MongoDB Offline (mock data)',
      ok: apiOnline,
      title: apiOnline ? 'API reachable, serving MongoDB' : 'API unreachable — using bundled mock dataset',
    },
    {
      icon: <Network size={14} />,
      label: graphStatus?.connected ? 'Neo4j Connected' : 'Neo4j Offline',
      ok: !!graphStatus?.connected,
      title: graphStatus?.connected
        ? `${graphStatus.relationships ?? 0} relationships projected`
        : graphStatus?.reason || 'Not connected',
    },
    {
      icon: <Activity size={14} />,
      label: modelInfo?.available ? 'Risk Model Loaded' : 'Risk Model: heuristic',
      ok: !!modelInfo?.available,
      title: modelInfo?.available
        ? `${modelInfo.source} — accuracy ${(modelInfo.accuracy * 100).toFixed(1)}%`
        : 'scikit-learn model unavailable; weighted-sum fallback in use',
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

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return children;
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
            <Route path="/" element={<Dashboard />} />
            <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
            <Route path="/reconciliation" element={<Reconciliation />} />
            <Route path="/itc-risk" element={<ITCRisk />} />
            <Route path="/audit-trails" element={<AuditTrails />} />
            <Route path="/vendor-compliance" element={<VendorCompliance />} />
            <Route path="/data-entry" element={<DataEntry />} />
            <Route path="/settings" element={<Settings />} />
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
