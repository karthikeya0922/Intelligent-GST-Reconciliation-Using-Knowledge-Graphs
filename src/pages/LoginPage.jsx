import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Zap, Network, ShieldCheck, Brain } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const [isSignup, setIsSignup] = useState(false);
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login, signup } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        // Simulate network delay
        await new Promise(r => setTimeout(r, 800));

        let result;
        if (isSignup) {
            if (!name.trim()) { setError('Name is required'); setIsLoading(false); return; }
            if (password.length < 6) { setError('Password must be at least 6 characters'); setIsLoading(false); return; }
            result = signup(name, email, password);
        } else {
            result = login(email, password);
        }

        if (!result.success) {
            setError(result.error);
        }
        setIsLoading(false);
    };

    const fillDemo = (type) => {
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
        { icon: <Network size={20} />, title: 'Knowledge Graph', desc: 'Neo4j-powered entity modeling' },
        { icon: <ShieldCheck size={20} />, title: 'Smart Reconciliation', desc: 'Graph traversal mismatch detection' },
        { icon: <Brain size={20} />, title: 'AI Audit Trails', desc: 'LLM-generated explanations' },
    ];

    return (
        <div className="login-page">
            {/* Left Panel - Branding */}
            <div className="login-left">
                <div className="login-brand">
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="login-logo">
                            <Zap size={32} />
                            <h1>GST ReconcileAI</h1>
                        </div>
                        <p className="login-tagline">Intelligent GST Reconciliation<br />Using Knowledge Graphs</p>
                    </motion.div>

                    <motion.div
                        className="login-features"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3, duration: 0.6 }}
                    >
                        {features.map((f, i) => (
                            <motion.div
                                key={i}
                                className="login-feature"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.4 + i * 0.15 }}
                            >
                                <div className="login-feature-icon">{f.icon}</div>
                                <div>
                                    <h4>{f.title}</h4>
                                    <p>{f.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </motion.div>

                    <div className="login-footer-text">
                        <p>Problem #76 • FinTech / GovTech / Graph AI</p>
                    </div>
                </div>
            </div>

            {/* Right Panel - Form */}
            <div className="login-right">
                <motion.div
                    className="login-form-container"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5 }}
                >
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={isSignup ? 'signup' : 'login'}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <h2>{isSignup ? 'Create Account' : 'Welcome Back'}</h2>
                            <p className="login-subtitle">
                                {isSignup
                                    ? 'Sign up to access the GST reconciliation engine'
                                    : 'Sign in to your GST ReconcileAI dashboard'}
                            </p>

                            <form onSubmit={handleSubmit} className="login-form">
                                {isSignup && (
                                    <div className="form-group">
                                        <label>Full Name</label>
                                        <div className="input-wrapper">
                                            <User size={16} className="input-icon" />
                                            <input
                                                type="text"
                                                placeholder="Enter your name"
                                                value={name}
                                                onChange={(e) => setName(e.target.value)}
                                                required={isSignup}
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="form-group">
                                    <label>Email</label>
                                    <div className="input-wrapper">
                                        <Mail size={16} className="input-icon" />
                                        <input
                                            type="email"
                                            placeholder="Enter your email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Password</label>
                                    <div className="input-wrapper">
                                        <Lock size={16} className="input-icon" />
                                        <input
                                            type={showPassword ? 'text' : 'password'}
                                            placeholder="Enter your password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                        />
                                        <button
                                            type="button"
                                            className="password-toggle"
                                            onClick={() => setShowPassword(!showPassword)}
                                        >
                                            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                        </button>
                                    </div>
                                </div>

                                {error && (
                                    <motion.div
                                        className="form-error"
                                        initial={{ opacity: 0, y: -5 }}
                                        animate={{ opacity: 1, y: 0 }}
                                    >
                                        {error}
                                    </motion.div>
                                )}

                                <button type="submit" className="btn-login" disabled={isLoading}>
                                    {isLoading ? (
                                        <div className="spinner"></div>
                                    ) : (
                                        <>
                                            {isSignup ? 'Create Account' : 'Sign In'}
                                            <ArrowRight size={16} />
                                        </>
                                    )}
                                </button>
                            </form>

                            {!isSignup && (
                                <div className="demo-accounts">
                                    <p>Quick demo login:</p>
                                    <div className="demo-buttons">
                                        <button className="demo-btn" onClick={() => fillDemo('admin')}>
                                            Admin Account
                                        </button>
                                        <button className="demo-btn" onClick={() => fillDemo('auditor')}>
                                            Auditor Account
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div className="login-switch">
                                {isSignup ? (
                                    <p>Already have an account? <button onClick={() => { setIsSignup(false); setError(''); }}>Sign In</button></p>
                                ) : (
                                    <p>Don't have an account? <button onClick={() => { setIsSignup(true); setError(''); }}>Sign Up</button></p>
                                )}
                            </div>
                        </motion.div>
                    </AnimatePresence>
                </motion.div>
            </div>
        </div>
    );
}
