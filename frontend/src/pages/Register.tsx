import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Register() {
    const [formData, setFormData] = useState({
        full_name: '', phone_number: '', password: '',
        role: 'RESIDENT', latitude: 25.5788, longitude: 91.8933,
        locality: 'Laitumkhrah', district: 'East Khasi Hills', state: 'Meghalaya'
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await register(formData);
            navigate('/login');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="w-full max-w-lg mx-auto pt-10">
            <div className="card">
                <h2 className="text-2xl font-bold text-center mb-6">Register for TerraGuard</h2>

                {error && <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg mb-6 text-sm">{error}</div>}

                <form onSubmit={handleRegister} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="label">Full Name</label>
                            <input type="text" className="input-field" value={formData.full_name} onChange={e => setFormData({ ...formData, full_name: e.target.value })} required />
                        </div>
                        <div>
                            <label className="label">Phone Number</label>
                            <input type="text" className="input-field" value={formData.phone_number} onChange={e => setFormData({ ...formData, phone_number: e.target.value })} placeholder="+91..." required />
                        </div>
                    </div>

                    <div>
                        <label className="label">Password</label>
                        <input type="password" className="input-field" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required />
                    </div>

                    <div className="pt-4 border-t border-slate-700">
                        <label className="label mb-2 text-terra-400">PostGIS Setup (Simulated Location)</label>
                        <p className="text-xs text-slate-400 mb-3">To demonstrate TerraGuard's PostGIS spatial targeting, please select your simulated location.</p>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                            <button type="button" onClick={() => setFormData({ ...formData, latitude: 25.5788, longitude: 91.8933, locality: 'Shillong East' })} className={`py-2 rounded-lg text-sm border font-mono ${formData.latitude === 25.5788 ? 'bg-terra-500/20 border-terra-500 text-terra-300' : 'border-slate-700 text-slate-400 hover:border-slate-500'}`}>
                                SHILLONG (ZONE A)
                            </button>
                            <button type="button" onClick={() => setFormData({ ...formData, latitude: 26.1158, longitude: 91.7086, locality: 'Guwahati' })} className={`py-2 rounded-lg text-sm border font-mono ${formData.latitude === 26.1158 ? 'bg-terra-500/20 border-terra-500 text-terra-300' : 'border-slate-700 text-slate-400 hover:border-slate-500'}`}>
                                GUWAHATI (OUTSIDE)
                            </button>
                        </div>
                    </div>

                    <button type="submit" disabled={loading} className="btn-primary w-full mt-4">
                        {loading ? 'Registering...' : 'Complete Registration'}
                    </button>
                </form>
            </div>
        </div>
    );
}
