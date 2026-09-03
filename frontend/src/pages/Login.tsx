import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Login() {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(phone, password);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full max-w-md mx-auto pt-16">
            <div className="card">
                <h2 className="text-2xl font-bold text-center mb-6">Command Center Login</h2>

                {error && <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg mb-6 text-sm">{error}</div>}

                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="label">Phone Number</label>
                        <input
                            type="text"
                            className="input-field"
                            value={phone}
                            onChange={e => setPhone(e.target.value)}
                            placeholder="+919876543210"
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Password</label>
                        <input
                            type="password"
                            className="input-field"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button type="submit" disabled={loading} className="btn-primary w-full mt-4">
                        {loading ? 'Authenticating...' : 'Secure Login'}
                    </button>
                </form>

                <div className="mt-8 pt-6 border-t border-slate-800 text-center text-sm text-slate-400">
                    <p>Demo accounts (pwd: role+123):</p>
                    <div className="mt-2 font-mono text-xs space-y-1 text-slate-500">
                        <p>Admin: +919876543200</p>
                        <p>Authority: +919876543220</p>
                        <p>Resident inside zone: +919876543210</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
