import { useState } from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon, User, Bell, Database, Shield, Palette, Globe, Save, LogOut, ChevronRight, Check, Monitor } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
    const { theme, setTheme, toggleTheme } = useTheme();
    const { user, logout, updateProfile } = useAuth();

    const [activeTab, setActiveTab] = useState('appearance');
    const [profileName, setProfileName] = useState(user?.name || '');
    const [profileEmail, setProfileEmail] = useState(user?.email || '');
    const [saved, setSaved] = useState(false);

    // Settings state
    const [settings, setSettings] = useState(() => {
        const stored = localStorage.getItem('gst-settings');
        return stored ? JSON.parse(stored) : {
            notifications: { email: true, browser: true, mismatchAlerts: true, weeklyDigest: true, riskThresholdAlert: true },
            reconciliation: { autoPeriod: '2025-07', autoReconcile: false, riskThreshold: 60, hideMatched: false, groupByVendor: true },
            graph: { neo4jUri: 'bolt://localhost:7687', neo4jUser: 'neo4j', maxNodes: 200, animateEdges: true, showLabels: true },
            llm: { provider: 'openai', model: 'gpt-4', temperature: 0, maxTokens: 1024 },
            display: { currency: 'INR', dateFormat: 'DD-MM-YYYY', language: 'en', compactTables: false, showGSTIN: true },
        };
    });

    const saveSettings = () => {
        localStorage.setItem('gst-settings', JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const saveProfile = () => {
        updateProfile({ name: profileName, email: profileEmail });
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    const updateSetting = (category, key, value) => {
        setSettings(prev => ({
            ...prev,
            [category]: { ...prev[category], [key]: value }
        }));
    };

    const tabs = [
        { id: 'appearance', icon: <Palette size={18} />, label: 'Appearance' },
        { id: 'profile', icon: <User size={18} />, label: 'Profile' },
        { id: 'notifications', icon: <Bell size={18} />, label: 'Notifications' },
        { id: 'reconciliation', icon: <Shield size={18} />, label: 'Reconciliation' },
        { id: 'database', icon: <Database size={18} />, label: 'Database' },
        { id: 'display', icon: <Globe size={18} />, label: 'Display' },
    ];

    const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.05 } } };
    const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <div className="page-header-row">
                    <div>
                        <h2>⚙️ Settings</h2>
                        <p>Configure your dashboard preferences and system settings</p>
                    </div>
                    <button className="btn btn-primary" onClick={saveSettings}>
                        {saved ? <><Check size={16} /> Saved!</> : <><Save size={16} /> Save Changes</>}
                    </button>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '20px' }}>
                {/* Settings Sidebar */}
                <div className="card" style={{ padding: '12px', position: 'sticky', top: '24px', height: 'fit-content' }}>
                    {tabs.map(tab => (
                        <div
                            key={tab.id}
                            className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.icon}
                            {tab.label}
                        </div>
                    ))}
                    <hr style={{ border: 'none', borderTop: '1px solid var(--border-primary)', margin: '8px 0' }} />
                    <div className="nav-item" onClick={logout} style={{ color: 'var(--danger)' }}>
                        <LogOut size={18} />
                        Logout
                    </div>
                </div>

                {/* Settings Content */}
                <motion.div variants={container} initial="hidden" animate="show" key={activeTab}>

                    {/* Appearance */}
                    {activeTab === 'appearance' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>🎨 Appearance</h3>


                            <div className="settings-section">
                                <h4>Quick Toggle</h4>
                                <div className="setting-row">
                                    <div>
                                        <span>Dark Mode</span>
                                        <p className="settings-desc">Switch between light and dark themes</p>
                                    </div>
                                    <label className="toggle-switch">
                                        <input type="checkbox" checked={theme === 'dark'} onChange={toggleTheme} />
                                        <span className="toggle-slider">
                                            <Sun size={12} className="toggle-icon-left" />
                                            <Moon size={12} className="toggle-icon-right" />
                                        </span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Profile */}
                    {activeTab === 'profile' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>👤 Profile</h3>

                            <div className="settings-section">
                                <div className="profile-header">
                                    <div className="profile-avatar">
                                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                                    </div>
                                    <div>
                                        <h4>{user?.name}</h4>
                                        <p className="settings-desc">{user?.email}</p>
                                        <span className={`badge ${user?.role === 'admin' ? 'warning' : 'info'}`}>{user?.role}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="settings-section">
                                <div className="form-group">
                                    <label>Full Name</label>
                                    <input className="filter-input" style={{ width: '100%' }} value={profileName} onChange={(e) => setProfileName(e.target.value)} />
                                </div>
                                <div className="form-group" style={{ marginTop: '12px' }}>
                                    <label>Email</label>
                                    <input className="filter-input" style={{ width: '100%' }} value={profileEmail} onChange={(e) => setProfileEmail(e.target.value)} />
                                </div>
                                <button className="btn btn-primary mt-2" onClick={saveProfile}>
                                    {saved ? <><Check size={16} /> Updated!</> : 'Update Profile'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Notifications */}
                    {activeTab === 'notifications' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>🔔 Notifications</h3>

                            {[
                                { key: 'email', label: 'Email Notifications', desc: 'Receive reconciliation reports via email' },
                                { key: 'browser', label: 'Browser Notifications', desc: 'Get push notifications in your browser' },
                                { key: 'mismatchAlerts', label: 'Mismatch Alerts', desc: 'Alert when new mismatches are detected' },
                                { key: 'riskThresholdAlert', label: 'Risk Threshold Alerts', desc: 'Alert when vendor risk exceeds threshold' },
                                { key: 'weeklyDigest', label: 'Weekly Digest', desc: 'Weekly summary of reconciliation status' },
                            ].map(n => (
                                <motion.div key={n.key} className="setting-row" variants={item}>
                                    <div>
                                        <span>{n.label}</span>
                                        <p className="settings-desc">{n.desc}</p>
                                    </div>
                                    <label className="toggle-switch">
                                        <input type="checkbox" checked={settings.notifications[n.key]} onChange={(e) => updateSetting('notifications', n.key, e.target.checked)} />
                                        <span className="toggle-slider"></span>
                                    </label>
                                </motion.div>
                            ))}
                        </div>
                    )}

                    {/* Reconciliation */}
                    {activeTab === 'reconciliation' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>🔍 Reconciliation Settings</h3>

                            <div className="setting-row">
                                <div>
                                    <span>Auto-Reconcile on Data Load</span>
                                    <p className="settings-desc">Automatically run reconciliation when new data is ingested</p>
                                </div>
                                <label className="toggle-switch">
                                    <input type="checkbox" checked={settings.reconciliation.autoReconcile} onChange={(e) => updateSetting('reconciliation', 'autoReconcile', e.target.checked)} />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="setting-row">
                                <div>
                                    <span>Hide Matched Invoices</span>
                                    <p className="settings-desc">Only show mismatched entries in reconciliation view</p>
                                </div>
                                <label className="toggle-switch">
                                    <input type="checkbox" checked={settings.reconciliation.hideMatched} onChange={(e) => updateSetting('reconciliation', 'hideMatched', e.target.checked)} />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="setting-row">
                                <div>
                                    <span>Group by Vendor</span>
                                    <p className="settings-desc">Group reconciliation results by vendor</p>
                                </div>
                                <label className="toggle-switch">
                                    <input type="checkbox" checked={settings.reconciliation.groupByVendor} onChange={(e) => updateSetting('reconciliation', 'groupByVendor', e.target.checked)} />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="settings-section" style={{ marginTop: '16px' }}>
                                <div className="form-group">
                                    <label>Risk Threshold (%)</label>
                                    <p className="settings-desc">Vendors above this score are flagged as High Risk</p>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
                                        <input type="range" min="20" max="90" value={settings.reconciliation.riskThreshold} onChange={(e) => updateSetting('reconciliation', 'riskThreshold', parseInt(e.target.value))} style={{ flex: 1 }} />
                                        <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)', minWidth: '36px' }}>{settings.reconciliation.riskThreshold}%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="settings-section">
                                <div className="form-group">
                                    <label>Default Period</label>
                                    <select className="filter-select" style={{ width: '100%' }} value={settings.reconciliation.autoPeriod} onChange={(e) => updateSetting('reconciliation', 'autoPeriod', e.target.value)}>
                                        <option value="2025-07">July 2025</option>
                                        <option value="2025-08">August 2025</option>
                                        <option value="2025-09">September 2025</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Database */}
                    {activeTab === 'database' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>🗄️ Database & LLM Configuration</h3>

                            <div className="settings-section">
                                <h4>Neo4j Connection</h4>
                                <div className="form-group">
                                    <label>Connection URI</label>
                                    <input className="filter-input" style={{ width: '100%' }} value={settings.graph.neo4jUri} onChange={(e) => updateSetting('graph', 'neo4jUri', e.target.value)} />
                                </div>
                                <div className="form-group" style={{ marginTop: '8px' }}>
                                    <label>Username</label>
                                    <input className="filter-input" style={{ width: '100%' }} value={settings.graph.neo4jUser} onChange={(e) => updateSetting('graph', 'neo4jUser', e.target.value)} />
                                </div>
                                <div style={{ display: 'flex', gap: '12px', marginTop: '12px' }}>
                                    <div className="setting-row" style={{ flex: 1 }}>
                                        <div>
                                            <span>Animate Edges</span>
                                            <p className="settings-desc">Show particle animation on graph edges</p>
                                        </div>
                                        <label className="toggle-switch">
                                            <input type="checkbox" checked={settings.graph.animateEdges} onChange={(e) => updateSetting('graph', 'animateEdges', e.target.checked)} />
                                            <span className="toggle-slider"></span>
                                        </label>
                                    </div>
                                </div>
                                <div className="setting-row">
                                    <div>
                                        <span>Show Node Labels</span>
                                        <p className="settings-desc">Display labels on graph nodes</p>
                                    </div>
                                    <label className="toggle-switch">
                                        <input type="checkbox" checked={settings.graph.showLabels} onChange={(e) => updateSetting('graph', 'showLabels', e.target.checked)} />
                                        <span className="toggle-slider"></span>
                                    </label>
                                </div>
                                <div className="form-group" style={{ marginTop: '8px' }}>
                                    <label>Max Visible Nodes</label>
                                    <input type="number" className="filter-input" style={{ width: '100%' }} value={settings.graph.maxNodes} onChange={(e) => updateSetting('graph', 'maxNodes', parseInt(e.target.value))} />
                                </div>
                            </div>

                            <div className="settings-section" style={{ marginTop: '20px' }}>
                                <h4>LLM Configuration</h4>
                                <div className="form-group">
                                    <label>Provider</label>
                                    <select className="filter-select" style={{ width: '100%' }} value={settings.llm.provider} onChange={(e) => updateSetting('llm', 'provider', e.target.value)}>
                                        <option value="openai">OpenAI</option>
                                        <option value="azure">Azure OpenAI</option>
                                        <option value="anthropic">Anthropic</option>
                                        <option value="local">Local (Ollama)</option>
                                    </select>
                                </div>
                                <div className="form-group" style={{ marginTop: '8px' }}>
                                    <label>Model</label>
                                    <select className="filter-select" style={{ width: '100%' }} value={settings.llm.model} onChange={(e) => updateSetting('llm', 'model', e.target.value)}>
                                        <option value="gpt-4">GPT-4</option>
                                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                        <option value="claude-3-opus">Claude 3 Opus</option>
                                    </select>
                                </div>
                                <div className="form-group" style={{ marginTop: '8px' }}>
                                    <label>Temperature: {settings.llm.temperature}</label>
                                    <input type="range" min="0" max="100" value={settings.llm.temperature * 100} onChange={(e) => updateSetting('llm', 'temperature', parseInt(e.target.value) / 100)} style={{ width: '100%' }} />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Display */}
                    {activeTab === 'display' && (
                        <div className="card">
                            <h3 style={{ marginBottom: '20px' }}>🌐 Display Preferences</h3>

                            <div className="form-group">
                                <label>Currency</label>
                                <select className="filter-select" style={{ width: '100%' }} value={settings.display.currency} onChange={(e) => updateSetting('display', 'currency', e.target.value)}>
                                    <option value="INR">₹ Indian Rupee (INR)</option>
                                    <option value="USD">$ US Dollar (USD)</option>
                                    <option value="EUR">€ Euro (EUR)</option>
                                </select>
                            </div>

                            <div className="form-group" style={{ marginTop: '12px' }}>
                                <label>Date Format</label>
                                <select className="filter-select" style={{ width: '100%' }} value={settings.display.dateFormat} onChange={(e) => updateSetting('display', 'dateFormat', e.target.value)}>
                                    <option value="DD-MM-YYYY">DD-MM-YYYY</option>
                                    <option value="MM-DD-YYYY">MM-DD-YYYY</option>
                                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                                </select>
                            </div>

                            <div className="form-group" style={{ marginTop: '12px' }}>
                                <label>Language</label>
                                <select className="filter-select" style={{ width: '100%' }} value={settings.display.language} onChange={(e) => updateSetting('display', 'language', e.target.value)}>
                                    <option value="en">English</option>
                                    <option value="hi">Hindi</option>
                                    <option value="te">Telugu</option>
                                    <option value="ta">Tamil</option>
                                </select>
                            </div>

                            <div className="setting-row" style={{ marginTop: '16px' }}>
                                <div>
                                    <span>Compact Tables</span>
                                    <p className="settings-desc">Use smaller row heights in data tables</p>
                                </div>
                                <label className="toggle-switch">
                                    <input type="checkbox" checked={settings.display.compactTables} onChange={(e) => updateSetting('display', 'compactTables', e.target.checked)} />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>

                            <div className="setting-row">
                                <div>
                                    <span>Show Full GSTIN</span>
                                    <p className="settings-desc">Display complete GSTIN numbers in tables</p>
                                </div>
                                <label className="toggle-switch">
                                    <input type="checkbox" checked={settings.display.showGSTIN} onChange={(e) => updateSetting('display', 'showGSTIN', e.target.checked)} />
                                    <span className="toggle-slider"></span>
                                </label>
                            </div>
                        </div>
                    )}

                </motion.div>
            </div>
        </motion.div>
    );
}
