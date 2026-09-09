import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Mail,
    Lock,
    User,
    Eye,
    EyeOff,
    ArrowRight,
    Zap,
    Network,
    ShieldCheck,
    Brain,
    Building2,
    Briefcase,
    CheckCircle2,
    AlertCircle,
    KeyRound,
    Sparkles,
    HelpCircle,
    X,
    Database
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage({ initialMode = 'login' }) {
    const [isSignup, setIsSignup] = useState(initialMode === 'signup');
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [organization, setOrganization] = useState('');
    const [role, setRole] = useState('auditor');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [acceptedTerms, setAcceptedTerms] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showForgotModal, setShowForgotModal] = useState(false);
    const [activeDemo, setActiveDemo] = useState(null);

    const { login, signup, authOnline } = useAuth();

    useEffect(() => {
        setIsSignup(initialMode === 'signup');
        setError('');
        setSuccessMessage('');
    }, [initialMode]);

    // Password strength calculation
    const getPasswordStrength = (pwd) => {
        if (!pwd) return { score: 0, label: 'None', color: '#64748b' };
        let score = 0;
        if (pwd.length >= 6) score += 1;
        if (pwd.length >= 10) score += 1;
        if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1;
        if (/[0-9]/.test(pwd) || /[^A-Za-z0-9]/.test(pwd)) score += 1;

        switch (score) {
            case 1:
                return { score: 25, label: 'Weak', color: '#ef4444' };
            case 2:
                return { score: 50, label: 'Fair', color: '#f59e0b' };
            case 3:
                return { score: 75, label: 'Good', color: '#3b82f6' };
            case 4:
                return { score: 100, label: 'Strong', color: '#10b981' };
            default:
                return { score: 15, label: 'Too short', color: '#ef4444' };
        }
    };

    const pwdStrength = getPasswordStrength(password);
    const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;
    const passwordMismatch = confirmPassword.length > 0 && password !== confirmPassword;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');
        setIsLoading(true);

        let result;
        if (isSignup) {
            if (!name.trim()) {
                setError('Full name is required');
                setIsLoading(false);
                return;
            }
            if (password.length < 6) {
                setError('Password must be at least 6 characters');
                setIsLoading(false);
                return;
            }
            if (password !== confirmPassword) {
                setError('Passwords do not match');
                setIsLoading(false);
                return;
            }
            if (!acceptedTerms) {
                setError('Please acknowledge the Decision-Support platform terms to proceed');
                setIsLoading(false);
                return;
            }

            result = await signup(name.trim(), email.trim(), password, role, organization.trim() || 'GST Audit Division');
        } else {
            result = await login(email.trim(), password);
        }

        if (!result.success) {
            setError(result.error || 'Authentication failed');
        } else if (isSignup) {
            setSuccessMessage('Account created successfully! Loading your workspace...');
        }
        setIsLoading(false);
    };

    const fillDemo = (type) => {
        setActiveDemo(type);
        if (type === 'admin') {
            setEmail('admin@gstreconcile.ai');
            setPassword('admin123');
        } else {
            setEmail('auditor@gstreconcile.ai');
            setPassword('auditor123');
        }
        setError('');
    };

    const features = [
        {
            icon: <Brain size={20} />,
            title: 'Tabular XGBoost Risk Engine',
            desc: 'Calibrated 0–100 behavioral risk scoring with Tree SHAP factor breakdown'
        },
        {
            icon: <Network size={20} />,
            title: 'Knowledge Graph Investigation',
            desc: 'Multi-hop supplier-customer relationships and circular trading detection'
        },
        {
            icon: <ShieldCheck size={20} />,
            title: 'ITC Exposure Prioritization',
            desc: 'Decoupled financial materiality × behavioral risk operational matrix'
        },
    ];

    const stats = [
        { label: 'Monitored Vendors', value: '2,015' },
        { label: 'Reconciled Invoices', value: '168,213' },
        { label: 'Temporal Integrity', value: '100%' },
    ];

    return (
        <div className="login-page">
            {/* Left Panel - Research & Platform Branding */}
            <div className="login-left">
                <div className="login-brand">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="login-badge-tag">
                            <Sparkles size={13} />
                            <span>Enterprise GST Risk Intelligence</span>
                        </div>
                        <div className="login-logo">
                            <Zap size={34} className="logo-pulse" />
                            <h1>GST ReconcileAI</h1>
                        </div>
                        <p className="login-tagline">
                            Intelligent GST Reconciliation, ITC Exposure Analysis & Knowledge Graph Investigation
                        </p>
                    </motion.div>

                    {/* Live Stats Pill Banner */}
                    <motion.div
                        className="login-stats-row"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.5 }}
                    >
                        {stats.map((s, idx) => (
                            <div key={idx} className="login-stat-card">
                                <span className="stat-val">{s.value}</span>
                                <span className="stat-lbl">{s.label}</span>
                            </div>
                        ))}
                    </motion.div>

                    {/* Features List */}
                    <motion.div
                        className="login-features"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.35, duration: 0.6 }}
                    >
                        {features.map((f, i) => (
                            <motion.div
                                key={i}
                                className="login-feature"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.4 + i * 0.12 }}
                            >
                                <div className="login-feature-icon">{f.icon}</div>
                                <div>
                                    <h4>{f.title}</h4>
                                    <p>{f.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>

                    {/* System Status & Footer */}
                    <div className="login-footer-meta">
                        <div className="system-status-pill">
                            <span className="status-indicator-dot online"></span>
                            <span>{authOnline ? 'FastAPI Backend Online' : 'Offline Demo Mode Ready'}</span>
                        </div>
                        <p className="footer-disclaimer">
                            Research Benchmark • Problem #76 • FinTech & Graph AI
                        </p>
                    </div>
                </div>
            </div>

            {/* Right Panel - Login & Registration Form */}
            <div className="login-right">
                <motion.div
                    className="login-form-container"
                    initial={{ opacity: 0, scale: 0.96 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.45 }}
                >
                    {/* Top Mode Segmented Switcher */}
                    <div className="auth-tab-group">
                        <button
                            type="button"
                            className={`auth-tab-btn ${!isSignup ? 'active' : ''}`}
                            onClick={() => { setIsSignup(false); setError(''); setSuccessMessage(''); }}
                        >
                            Sign In
                        </button>
                        <button
                            type="button"
                            className={`auth-tab-btn ${isSignup ? 'active' : ''}`}
                            onClick={() => { setIsSignup(true); setError(''); setSuccessMessage(''); }}
                        >
                            Create Account
                        </button>
                    </div>

                    <AnimatePresence mode="wait">
                        <motion.div
                            key={isSignup ? 'signup' : 'login'}
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -12 }}
                            transition={{ duration: 0.25 }}
                        >
                            <div className="auth-header">
                                <h2>{isSignup ? 'Auditor Registration' : 'Welcome Back'}</h2>
                                <p className="login-subtitle">
                                    {isSignup
                                        ? 'Register to access GST reconciliation, SHAP risk predictions, and graph analytics'
                                        : 'Sign in to access your GST reconciliation workspace'}
                                </p>
                            </div>

                            <form onSubmit={handleSubmit} className="login-form">
                                {isSignup && (
                                    <>
                                        {/* Full Name */}
                                        <div className="form-group">
                                            <label>Full Name</label>
                                            <div className="input-wrapper">
                                                <User size={16} className="input-icon" />
                                                <input
                                                    type="text"
                                                    placeholder="e.g. Dr. Priya Sharma"
                                                    value={name}
                                                    onChange={(e) => setName(e.target.value)}
                                                    required={isSignup}
                                                    autoComplete="name"
                                                />
                                            </div>
                                        </div>

                                        {/* Organization & Professional Role Grid */}
                                        <div className="form-row-2">
                                            <div className="form-group">
                                                <label>Professional Role</label>
                                                <div className="input-wrapper">
                                                    <Briefcase size={16} className="input-icon" />
                                                    <select
                                                        value={role}
                                                        onChange={(e) => setRole(e.target.value)}
                                                        className="auth-select"
                                                    >
                                                        <option value="auditor">Tax Auditor</option>
                                                        <option value="compliance">Compliance Officer</option>
                                                        <option value="controller">Financial Controller</option>
                                                        <option value="investigator">Forensic Investigator</option>
                                                        <option value="admin">System Administrator</option>
                                                    </select>
                                                </div>
                                            </div>

                                            <div className="form-group">
                                                <label>Organization / Dept</label>
                                                <div className="input-wrapper">
                                                    <Building2 size={16} className="input-icon" />
                                                    <input
                                                        type="text"
                                                        placeholder="e.g. GST Audit Cell"
                                                        value={organization}
                                                        onChange={(e) => setOrganization(e.target.value)}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}

                                {/* Email */}
                                <div className="form-group">
                                    <label>Work Email</label>
                                    <div className="input-wrapper">
                                        <Mail size={16} className="input-icon" />
                                        <input
                                            type="email"
                                            placeholder="auditor@gstreconcile.ai"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            autoComplete="email"
                                        />
                                    </div>
                                </div>

                                {/* Password */}
                                <div className="form-group">
                                    <div className="label-row">
                                        <label>Password</label>
                                        {!isSignup && (
                                            <button
                                                type="button"
                                                className="forgot-password-link"
                                                onClick={() => setShowForgotModal(true)}
                                            >
                                                Forgot password?
                                            </button>
                                        )}
                                    </div>
                                    <div className="input-wrapper">
                                        <Lock size={16} className="input-icon" />
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            placeholder={isSignup ? 'Create secure password (min 6 chars)' : 'Enter your password'}
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            autoComplete={isSignup ? 'new-password' : 'current-password'}
                                        />
                                        <button
                                            type="button"
                                            className="password-toggle"
                                            onClick={() => setShowPassword(!showPassword)}
                                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                                        >
                                            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>

                                    {/* Password Strength Indicator (Signup only) */}
                                    {isSignup && password.length > 0 && (
                                        <div className="pwd-strength-container">
                                            <div className="pwd-strength-bar-bg">
                                                <div
                                                    className="pwd-strength-bar-fill"
                                                    style={{
                                                        width: `${pwdStrength.score}%`,
                                                        backgroundColor: pwdStrength.color,
                                                    }}
                                                />
                                            </div>
                                            <div className="pwd-strength-labels">
                                                <span>Strength: <strong style={{ color: pwdStrength.color }}>{pwdStrength.label}</strong></span>
                                                <span className="pwd-hint">Min 6 chars</span>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Confirm Password (Signup only) */}
                                {isSignup && (
                                    <div className="form-group">
                                        <label>Confirm Password</label>
                                        <div className="input-wrapper">
                                            <KeyRound size={16} className="input-icon" />
                                            <input
                                                type={showConfirmPassword ? 'text' : 'password'}
                                                placeholder="Re-enter password"
                                                value={confirmPassword}
                                                onChange={(e) => setConfirmPassword(e.target.value)}
                                                required={isSignup}
                                                autoComplete="new-password"
                                            />
                                            <button
                                                type="button"
                                                className="password-toggle"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                                            >
                                                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                            </button>
                                        </div>
                                        {passwordsMatch && (
                                            <div className="input-success-msg">
                                                <CheckCircle2 size={13} /> Passwords match
                                            </div>
                                        )}
                                        {passwordMismatch && (
                                            <div className="input-warning-msg">
                                                <AlertCircle size={13} /> Passwords do not match
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Terms & Responsible AI Checkbox (Signup only) */}
                                {isSignup && (
                                    <div className="auth-checkbox-group">
                                        <label className="auth-checkbox-label">
                                            <input
                                                type="checkbox"
                                                checked={acceptedTerms}
                                                onChange={(e) => setAcceptedTerms(e.target.checked)}
                                                required
                                            />
                                            <span>
                                                I understand that GST ReconcileAI is a <strong>decision-support and risk indicator platform</strong>, and does not determine statutory tax liability or criminal non-compliance.
                                            </span>
                                        </label>
                                    </div>
                                )}

                                {/* Error Notification */}
                                {error && (
                                    <motion.div
                                        className="form-error"
                                        initial={{ opacity: 0, y: -4 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        <AlertCircle size={15} />
                                        <span>{error}</span>
                                    </motion.div>
                                )}

                                {/* Success Notification */}
                                {successMessage && (
                                    <motion.div
                                        className="form-success"
                                        initial={{ opacity: 0, y: -4 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        <CheckCircle2 size={15} />
                                        <span>{successMessage}</span>
                                    </motion.div>
                                )}

                                {/* Submit Button */}
                                <button type="submit" className="btn-login" disabled={isLoading}>
                                    {isLoading ? (
                                        <div className="spinner"></div>
                                    ) : (
                                        <>
                                            {isSignup ? 'Complete Registration' : 'Sign In to Workspace'}
                                            <ArrowRight size={17} />
                                        </>
                                    )}
                                </button>
                            </form>

                            {/* Demo Accounts Quick-Fill Section */}
                            {!isSignup && (
                                <div className="demo-accounts-box">
                                    <div className="demo-header">
                                        <Sparkles size={14} className="demo-icon" />
                                        <span>Quick Demo Access</span>
                                    </div>
                                    <div className="demo-buttons-grid">
                                        <button
                                            type="button"
                                            className={`demo-pill ${activeDemo === 'admin' ? 'active' : ''}`}
                                            onClick={() => fillDemo('admin')}
                                        >
                                            <span className="demo-role-badge admin">ADMIN</span>
                                            <span className="demo-desc">admin@gstreconcile.ai</span>
                                        </button>
                                        <button
                                            type="button"
                                            className={`demo-pill ${activeDemo === 'auditor' ? 'active' : ''}`}
                                            onClick={() => fillDemo('auditor')}
                                        >
                                            <span className="demo-role-badge auditor">AUDITOR</span>
                                            <span className="demo-desc">auditor@gstreconcile.ai</span>
                                        </button>
                                    </div>
                                </div>
                            )}

                            {/* Bottom Switcher */}
                            <div className="login-switch">
                                {isSignup ? (
                                    <p>
                                        Already registered?{' '}
                                        <button
                                            type="button"
                                            onClick={() => { setIsSignup(false); setError(''); setSuccessMessage(''); }}
                                        >
                                            Sign In
                                        </button>
                                    </p>
                                ) : (
                                    <p>
                                        Need auditor credentials?{' '}
                                        <button
                                            type="button"
                                            onClick={() => { setIsSignup(true); setError(''); setSuccessMessage(''); }}
                                        >
                                            Create Account
                                        </button>
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    </AnimatePresence>
                </motion.div>
            </div>

            {/* Forgot Password Modal */}
            <AnimatePresence>
                {showForgotModal && (
                    <div className="auth-modal-overlay" onClick={() => setShowForgotModal(false)}>
                        <motion.div
                            className="auth-modal-content"
                            onClick={(e) => e.stopPropagation()}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                        >
                            <div className="modal-header">
                                <div className="modal-title">
                                    <HelpCircle size={20} className="modal-icon" />
                                    <h3>Account Access & Password Reset</h3>
                                </div>
                                <button
                                    type="button"
                                    className="modal-close-btn"
                                    onClick={() => setShowForgotModal(false)}
                                >
                                    <X size={18} />
                                </button>
                            </div>
                            <div className="modal-body">
                                <p>
                                    For research demo environments, pre-configured role credentials are built directly into the platform:
                                </p>
                                <div className="credentials-callout">
                                    <div><strong>Admin:</strong> <code>admin@gstreconcile.ai</code> / <code>admin123</code></div>
                                    <div><strong>Auditor:</strong> <code>auditor@gstreconcile.ai</code> / <code>auditor123</code></div>
                                </div>
                                <p className="modal-note">
                                    In production enterprise deployments, contact your system administrator or IT security desk to initiate an identity verification reset.
                                </p>
                            </div>
                            <div className="modal-footer">
                                <button
                                    type="button"
                                    className="btn-modal-action"
                                    onClick={() => {
                                        fillDemo('auditor');
                                        setShowForgotModal(false);
                                    }}
                                >
                                    Autofill Auditor Demo
                                </button>
                                <button
                                    type="button"
                                    className="btn-modal-secondary"
                                    onClick={() => setShowForgotModal(false)}
                                >
                                    Close
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}
