import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

const API = 'http://localhost:8000/api';
const SESSION_KEY = 'gst-current-user';
// Offline-only credential store. Used when the API is unreachable so the demo
// still runs; the API is always preferred, and it hashes with bcrypt server-side.
const LOCAL_DB_KEY = 'gst-users-db';

async function postJSON(path, body, timeoutMs = 6000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const res = await fetch(`${API}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
            signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } finally {
        clearTimeout(timer);
    }
}

// ---- Offline fallback store -------------------------------------------------
// Passwords here are not hashed - the browser has no bcrypt and this path exists
// only so the UI is demoable with the backend switched off. Treat these accounts
// as throwaway; real credentials live in MongoDB behind /api/login.
function getLocalDB() {
    const stored = localStorage.getItem(LOCAL_DB_KEY);
    if (stored) {
        try { return JSON.parse(stored); } catch { /* fall through to reseed */ }
    }
    const seed = [
        { id: 1, email: 'admin@gstreconcile.ai', password: 'admin123', name: 'Admin User', role: 'admin', createdAt: '2025-01-01' },
        { id: 2, email: 'auditor@gstreconcile.ai', password: 'auditor123', name: 'Tax Auditor', role: 'auditor', createdAt: '2025-03-15' },
    ];
    localStorage.setItem(LOCAL_DB_KEY, JSON.stringify(seed));
    return seed;
}

function saveLocalDB(db) {
    localStorage.setItem(LOCAL_DB_KEY, JSON.stringify(db));
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [authOnline, setAuthOnline] = useState(true);

    useEffect(() => {
        const session = localStorage.getItem(SESSION_KEY);
        if (session) {
            try {
                setUser(JSON.parse(session));
            } catch {
                localStorage.removeItem(SESSION_KEY);
            }
        }
        setLoading(false);
    }, []);

    const persist = (userData) => {
        setUser(userData);
        localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
    };

    const login = async (email, password) => {
        const normalized = (email || '').trim().toLowerCase();
        try {
            const data = await postJSON('/login', { email: normalized, password });
            setAuthOnline(true);
            if (!data.success) return { success: false, error: data.error };
            persist(data.user);
            return { success: true };
        } catch {
            // API unreachable - fall back to the local store.
            setAuthOnline(false);
            const found = getLocalDB().find(u => u.email === normalized && u.password === password);
            if (!found) return { success: false, error: 'Invalid email or password' };
            persist({ id: found.id, email: found.email, name: found.name, role: found.role });
            return { success: true, offline: true };
        }
    };

    const signup = async (name, email, password) => {
        const normalized = (email || '').trim().toLowerCase();
        try {
            const data = await postJSON('/signup', { name, email: normalized, password });
            setAuthOnline(true);
            if (!data.success) return { success: false, error: data.error };
            persist(data.user);
            return { success: true };
        } catch {
            setAuthOnline(false);
            const db = getLocalDB();
            if (db.find(u => u.email === normalized)) {
                return { success: false, error: 'Email already registered' };
            }
            const newUser = {
                id: db.length + 1, email: normalized, password, name, role: 'user',
                createdAt: new Date().toISOString().split('T')[0],
            };
            db.push(newUser);
            saveLocalDB(db);
            persist({ id: newUser.id, email: newUser.email, name: newUser.name, role: newUser.role });
            return { success: true, offline: true };
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem(SESSION_KEY);
    };

    const updateProfile = async (updates) => {
        if (!user) return { success: false, error: 'Not signed in' };
        try {
            const data = await postJSON('/profile', { currentEmail: user.email, ...updates });
            setAuthOnline(true);
            if (!data.success) return { success: false, error: data.error };
            persist(data.user);
            return { success: true };
        } catch {
            setAuthOnline(false);
            const db = getLocalDB();
            const idx = db.findIndex(u => u.email === user.email);
            if (idx !== -1) {
                db[idx] = { ...db[idx], ...updates };
                saveLocalDB(db);
                persist({ id: db[idx].id, email: db[idx].email, name: db[idx].name, role: db[idx].role });
            }
            return { success: true, offline: true };
        }
    };

    const changePassword = async (currentPassword, newPassword) => {
        if (!user) return { success: false, error: 'Not signed in' };
        try {
            const data = await postJSON('/change-password', {
                email: user.email, currentPassword, newPassword,
            });
            return data.success ? { success: true } : { success: false, error: data.error };
        } catch {
            return { success: false, error: 'Password changes require the API to be running' };
        }
    };

    return (
        <AuthContext.Provider value={{
            user, loading, authOnline, login, signup, logout, updateProfile, changePassword,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
