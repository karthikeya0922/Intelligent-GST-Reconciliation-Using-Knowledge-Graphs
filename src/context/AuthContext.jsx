import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

// Static user database (simulates a database)
const STATIC_DB_KEY = 'gst-users-db';
const SESSION_KEY = 'gst-current-user';

function getDB() {
    const stored = localStorage.getItem(STATIC_DB_KEY);
    if (stored) return JSON.parse(stored);
    // Default admin account
    const defaultDB = [
        { id: 1, email: 'admin@gstreconcile.ai', password: 'admin123', name: 'Admin User', role: 'admin', createdAt: '2025-01-01' },
        { id: 2, email: 'auditor@gstreconcile.ai', password: 'auditor123', name: 'Tax Auditor', role: 'auditor', createdAt: '2025-03-15' },
    ];
    localStorage.setItem(STATIC_DB_KEY, JSON.stringify(defaultDB));
    return defaultDB;
}

function saveDB(db) {
    localStorage.setItem(STATIC_DB_KEY, JSON.stringify(db));
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing session
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

    const login = (email, password) => {
        const db = getDB();
        const found = db.find(u => u.email === email && u.password === password);
        if (!found) {
            return { success: false, error: 'Invalid email or password' };
        }
        const userData = { id: found.id, email: found.email, name: found.name, role: found.role };
        setUser(userData);
        localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
        return { success: true };
    };

    const signup = (name, email, password) => {
        const db = getDB();
        if (db.find(u => u.email === email)) {
            return { success: false, error: 'Email already registered' };
        }
        const newUser = {
            id: db.length + 1,
            email,
            password,
            name,
            role: 'user',
            createdAt: new Date().toISOString().split('T')[0],
        };
        db.push(newUser);
        saveDB(db);
        const userData = { id: newUser.id, email: newUser.email, name: newUser.name, role: newUser.role };
        setUser(userData);
        localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
        return { success: true };
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem(SESSION_KEY);
    };

    const updateProfile = (updates) => {
        const db = getDB();
        const idx = db.findIndex(u => u.id === user.id);
        if (idx !== -1) {
            db[idx] = { ...db[idx], ...updates };
            saveDB(db);
            const userData = { id: db[idx].id, email: db[idx].email, name: db[idx].name, role: db[idx].role };
            setUser(userData);
            localStorage.setItem(SESSION_KEY, JSON.stringify(userData));
        }
        return { success: true };
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, signup, logout, updateProfile }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
}
