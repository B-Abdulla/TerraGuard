import { useState, useEffect } from 'react';
import api from '../api';
import GISMap from '../components/GISMap';

export default function AuthorityCommandCenter() {
    const [data, setData] = useState<any>({ zones: [], alerts: [], reports: [], users: [] });
    const [loading, setLoading] = useState(true);

    // Auto-refresh data every 5s
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [z, a, r, u] = await Promise.all([
                    api.get('/risk/zones'),
                    api.get('/alerts'),
                    api.get('/community-reports'),
                    api.get('/system/users')
                ]);
                setData({
                    zones: z.data.zones,
                    alerts: a.data.alerts,
                    reports: r.data.reports,
                    users: u.data.users
                });
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleVerify = async (reportId: string, status: string) => {
        try {
            await api.post(`/community-reports/${reportId}/verify`, { status, notes: `Verified by command center` });
            // Trigger a quick reload
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <div className="text-center font-mono mt-20">CONNECTING_COMMAND_LINK...</div>;

    const criticalZones = data.zones.filter((z: any) => z.risk_level === 'CRITICAL');
    const highZones = data.zones.filter((z: any) => z.risk_level === 'HIGH');
    const pendingReports = data.reports.filter((r: any) => r.status === 'PENDING');

    return (
        <div className="w-full flex flex-col gap-6">

            {/* Top Banner Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card flex flex-col items-center justify-center py-4 bg-red-900/10 border-red-900/50">
                    <span className="text-4xl font-bold tracking-tighter text-red-500">{criticalZones.length}</span>
                    <span className="text-xs font-mono text-red-300 mt-1 uppercase">Critical Zones</span>
                </div>
                <div className="card flex flex-col items-center justify-center py-4 bg-orange-900/10 border-orange-900/50">
                    <span className="text-4xl font-bold tracking-tighter text-orange-400">{highZones.length}</span>
                    <span className="text-xs font-mono text-orange-300 mt-1 uppercase">High Risk Zones</span>
                </div>
                <div className="card flex flex-col items-center justify-center py-4">
                    <span className="text-4xl font-bold tracking-tighter text-terra-400">{data.alerts.length}</span>
                    <span className="text-xs font-mono text-slate-400 mt-1 uppercase">Alerts Sent</span>
                </div>
                <div className="card flex flex-col items-center justify-center py-4">
                    <span className="text-4xl font-bold tracking-tighter text-yellow-400">{pendingReports.length}</span>
                    <span className="text-xs font-mono text-slate-400 mt-1 uppercase">Pending Reports</span>
                </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">

                {/* Left Column: Map */}
                <div className="flex-1 flex flex-col gap-6">
                    <div className="card flex-1 min-h-[500px] p-0 overflow-hidden relative">
                        <div className="absolute top-4 left-4 z-[400] bg-slate-900/80 backdrop-blur px-3 py-2 rounded-lg border border-slate-700 text-xs font-mono">
                            SITUATIONAL OVERVIEW
                        </div>
                        <GISMap
                            center={[25.7, 91.8]}
                            zoom={10}
                            zones={data.zones}
                            reports={data.reports}
                            users={data.users}
                            height="100%"
                        />
                    </div>
                </div>

                {/* Right Column: Panels */}
                <div className="w-full lg:w-96 flex flex-col gap-6 h-full lg:max-h-[600px] lg:overflow-y-auto pr-2">

                    {/* Active Zones Panel */}
                    <div className="card">
                        <h2 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider border-b border-slate-700 pb-2">Active Risk Zones</h2>
                        <div className="space-y-3">
                            {data.zones.length === 0 && <p className="text-xs text-slate-500">No active zones detected.</p>}
                            {data.zones.map((z: any) => (
                                <div key={z.id} className="bg-slate-800/50 p-3 rounded border border-slate-700">
                                    <div className="flex justify-between items-start">
                                        <span className="font-bold text-sm tracking-tight">{z.name}</span>
                                        <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${z.risk_level === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'}`}>
                                            {z.risk_level}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-xs font-mono text-slate-400 flex justify-between">
                                        <span>Score: {z.risk_score.toFixed(2)}</span>
                                        <span>Affected target: {z.affected_users_count} users</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Reports Panel */}
                    <div className="card">
                        <h2 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider border-b border-slate-700 pb-2">Ground Feedback</h2>
                        <div className="space-y-3">
                            {data.reports.length === 0 && <p className="text-xs text-slate-500">No community feedback.</p>}
                            {data.reports.map((r: any) => (
                                <div key={r.id} className={`bg-slate-800/50 p-3 rounded border ${r.status === 'PENDING' ? 'border-yellow-500/30' : 'border-slate-700'}`}>
                                    <div className="text-xs font-bold text-slate-300 mb-1">{r.category}</div>
                                    <div className="text-xs text-slate-400 mb-2">"{r.description}"</div>

                                    {r.status === 'PENDING' ? (
                                        <div className="flex gap-2 mt-3">
                                            <button onClick={() => handleVerify(r.id, 'VERIFIED')} className="flex-1 bg-terra-600 hover:bg-terra-500 text-white text-[10px] py-1.5 rounded font-bold uppercase transition-colors">Verify</button>
                                            <button onClick={() => handleVerify(r.id, 'REJECTED')} className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-[10px] py-1.5 rounded font-bold uppercase transition-colors">Reject</button>
                                        </div>
                                    ) : (
                                        <div className="text-[10px] font-mono text-terra-500 uppercase mt-2 border-t border-slate-800 pt-2">Status: {r.status}</div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
