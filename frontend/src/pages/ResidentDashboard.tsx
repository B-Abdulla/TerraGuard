import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import api from '../api';
import GISMap from '../components/GISMap';

export default function ResidentDashboard() {
    const { user } = useAuth();
    const [alerts, setAlerts] = useState<any[]>([]);
    const [zones, setZones] = useState<any[]>([]);
    const [reportText, setReportText] = useState('');
    const [reportCat, setReportCat] = useState('GROUND_CRACK');
    const [rSubmitting, setRSubmitting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const aRes = await api.get('/alerts');
                setAlerts(aRes.data.alerts || []);

                const zRes = await api.get('/risk/zones');
                setZones(zRes.data.zones || []);
            } catch (e) {
                console.error("Dashboard fetch error", e);
            }
        };
        fetchData();
    }, []);

    const handleReport = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setRSubmitting(true);
        try {
            await api.post('/community-reports', {
                category: reportCat,
                description: reportText,
                latitude: user.latitude,
                longitude: user.longitude,
            });
            setReportText('');
            alert("Report submitted for verification. Thank you.");
        } catch (err) {
            alert("Failed to submit report.");
        } finally {
            setRSubmitting(false);
        }
    };

    const activeAlerts = alerts.filter(a => a.status === 'SENT' || a.status === 'DEMO');

    return (
        <div className="w-full flex gap-6 flex-col lg:flex-row">
            <div className="flex-1 space-y-6">

                {/* Alerts Section */}
                <div className="card">
                    <h2 className="text-xl font-bold mb-4 border-b border-slate-700 pb-2">Active Alerts</h2>
                    {activeAlerts.length === 0 ? (
                        <p className="text-slate-400">No active alerts for your area.</p>
                    ) : (
                        <div className="space-y-3">
                            {activeAlerts.map(a => (
                                <div key={a.id} className={`p-4 rounded-lg border flex flex-col ${a.risk_level === 'CRITICAL' ? 'bg-red-900/20 border-red-500/50' : 'bg-orange-900/20 border-orange-500/50'
                                    }`}>
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="font-bold tracking-wider text-sm flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                            {a.risk_level} ALERT
                                        </span>
                                        <span className="text-xs bg-black/30 px-2 py-1 rounded text-slate-300 font-mono">STATUS: {a.status}</span>
                                    </div>
                                    <p className="text-slate-200">{a.message}</p>
                                    <p className="text-xs text-slate-400 mt-3 font-mono">{new Date(a.created_at).toLocaleString()}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Map Section */}
                <div className="card">
                    <h2 className="text-xl font-bold mb-4 border-b border-slate-700 pb-2">Local Risk Map</h2>
                    <GISMap
                        center={[user?.latitude || 25.5788, user?.longitude || 91.8933]}
                        zones={zones}
                        users={user ? [user] : []}
                        height="350px"
                        zoom={13}
                    />
                </div>

            </div>

            <div className="w-full lg:w-96 space-y-6">
                {/* Community Report */}
                <div className="card">
                    <h2 className="text-xl font-bold mb-4 border-b border-slate-700 pb-2">Submit Observation</h2>
                    <form onSubmit={handleReport} className="space-y-4">
                        <div>
                            <label className="label">Category</label>
                            <select className="input-field" value={reportCat} onChange={e => setReportCat(e.target.value)}>
                                <option value="LANDSLIDE">Landslide / Rockfall</option>
                                <option value="GROUND_CRACK">Ground Crack</option>
                                <option value="ROAD_BLOCKAGE">Road Blockage</option>
                                <option value="HEAVY_RAINFALL">Extreme Rainfall</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Description</label>
                            <textarea
                                className="input-field h-24"
                                value={reportText} onChange={e => setReportText(e.target.value)}
                                placeholder="Describe the observation..."
                                required
                            ></textarea>
                        </div>
                        <button type="submit" className="btn-primary w-full" disabled={rSubmitting}>
                            {rSubmitting ? 'Submitting...' : 'Submit Report'}
                        </button>
                    </form>
                </div>

                {/* Location Info */}
                <div className="card bg-slate-800/40">
                    <h3 className="font-semibold mb-2">Registered Location</h3>
                    <div className="text-sm text-slate-300 font-mono space-y-1">
                        <p>LAT: {user?.latitude}</p>
                        <p>LNG: {user?.longitude}</p>
                        <p>LOC: {user?.locality}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
