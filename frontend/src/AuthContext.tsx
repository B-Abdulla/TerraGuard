import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from './api';

interface User {
    id: string;
    full_name: string;
    phone_number: string;
    email?: string;
    role: string;
    latitude?: number;
    longitude?: number;
    locality?: string;
    district?: string;
    state?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (phone: string, password: string) => Promise<void>;
    register: (data: any) => Promise<void>;
    logout: () => void;
    isAuth: boolean;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('terraguard_token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (token) {
            api.get('/auth/me')
                .then((r) => setUser(r.data))
                .catch(() => { setToken(null); localStorage.removeItem('terraguard_token'); })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [token]);

    const login = async (phone: string, password: string) => {
        const res = await api.post('/auth/login', { phone_number: phone, password });
        const t = res.data.access_token;
        localStorage.setItem('terraguard_token', t);
        setToken(t);
        const me = await api.get('/auth/me', { headers: { Authorization: `Bearer ${t}` } });
        setUser(me.data);
    };

    const register = async (data: any) => {
        await api.post('/auth/register', data);
    };

    const logout = () => {
        localStorage.removeItem('terraguard_token');
        localStorage.removeItem('terraguard_user');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, register, logout, isAuth: !!user, loading }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
    return ctx;
}
